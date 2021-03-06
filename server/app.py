import os 
import ntpath 
import mimetypes
import dropbox 
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from logging.config import dictConfig
import clamd

from werkzeug.utils import secure_filename

from rq import Queue
from rq.job import Job
from worker import conn
from config_variables import config


# config
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'filename': 'audio-spread.log',
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})


app = Flask(__name__, static_folder='../build')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'upload_tmp/'
CORS(app)

app.logger.info('connecting to Redis queue')
q = Queue(connection=conn)

# clamd init
app.logger.info('initializing Clamav')
try:
  cd = clamd.ClamdUnixSocket()
  cd.ping()
except:
  app.logger.error('could not open clamd unix socket. attemping network socket')
  cd = clamd.ClamdNetworkSocket()
  try:
    cd.ping()
  except clamd.ConnectionError:
    app.logger.error('could not connect to clamd server either by unix or network socket. go big or go home I guess.')
    cd = None 

# dropbox init
app.logger.info('initializing Dropbox')
dbx = dropbox.Dropbox(config['DROPBOX_ACCESS_TOKEN'])

def isaudio(file):
  return 'audio/' in file.mimetype

def has_virus(file_path):
  if cd is None:
    return False 
  app.logger.info('scanning for viruses')
  result = cd.scan(os.path.abspath(file_path))
  app.logger.info('scanned for viruses')
  app.logger.info('scan results: %s, %s' % (result[os.path.abspath(file_path)][0], result[os.path.abspath(file_path)][1]))
  return result[os.path.abspath(file_path)][1] is not None 

def errormessage(message, status_code):
  resp = jsonify({'message': message})
  resp.status_code = status_code
  return resp 

def save_to_dropbox(file_path):
  # TODO work on this
  app.logger.info('saving to dropbox')
  with open(os.path.abspath(file_path), 'rb') as file:
    contents = file.read()
    dbx.files_upload(contents, '/' + ntpath.basename(file_path))


def process_file(file_path):
  app.logger.info('processing %s' % ntpath.basename(file_path))
  
  if not has_virus(file_path):
    save_to_dropbox(file_path)
  else:
    app.logger.info('%s is suspected to be a virus. deleting' % ntpath.basename(file_path))

##
# API routes
##
@app.route('/api/upload', methods=['POST'])
def upload():
  
  name = request.args.get('name', 'unknown')
  email = request.args.get('email', 'unknown')

  if 'file' not in request.files:
    app.logger.error('No file part in the request')
    return errormessage('No file part in the request', 400)
  
  file = request.files['file']
  if file.filename == '':
    app.logger.error('No file selected for uploading')
    return errormessage('No file selected for uploading', 400) 

  if not isaudio(file):
    app.logger.error('file %s has mimetype %s. not audio' % (file.filename, file.mimetype))
    return errormessage('not audio', 400)
  

  # save file to directory
  filename = name + '-' + email + '-' + secure_filename(file.filename)
  upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
  file.save(upload_path)

  # process file
  from app import process_file

  job = q.enqueue_call(
    func=process_file, args=(upload_path,), result_ttl=5000
  )
  print(job.get_id())

  return jsonify({
    'message': 'Uploaded successfully.'
  })


##
# View route
##

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
  '''Return index.html for all non-api routes'''
  #pylint: disable=unused-argument
  return send_from_directory(app.static_folder, 'index.html')


  
  