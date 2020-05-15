import config
import os 
import ntpath 
import mimetypes
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from celery_app import process_file
from logging.config import dictConfig
from datetime import datetime
from werkzeug.utils import secure_filename

def isaudio(file):
  return 'audio/' in file.mimetype

def errormessage(message, status_code):
  resp = jsonify({'message': message})
  resp.status_code = status_code
  return resp 


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


# app
app = Flask(__name__, static_folder='../build')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'upload_tmp/'
app.config.update(
  CELERY_BROKER_URL=config.CELERY_BROKER_URL,
  CELERY_RESULT_BACKEND=config.CELERY_RESULT_BACKEND
)
CORS(app)

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
  dateTimeObj = datetime.now()
 
  timestampStr = dateTimeObj.strftime("%d-%b-%Y (%H:%M:%S.%f)")
  filename = timestampStr + '-' + name + '-' + email + '-' + secure_filename(file.filename)
  upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
  file.save(upload_path)

  # process file
  process_file.delay(upload_path)

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


if __name__ == '__main__':
    app.run()