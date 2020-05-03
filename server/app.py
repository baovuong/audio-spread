from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='../build')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
CORS(app)

def isaudio(file):
  return 'audio/' in file.mimetype

def isvirus(file):
  return False 

def errormessage(message, status_code):
  resp = jsonify({'message': message})
  resp.status_code = status_code
  return resp 

##
# API routes
##
@app.route('/api/upload', methods=['POST'])
def upload():
  
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
  
  # process file
  app.logger.info('file being processed. (%s, %s)' % (file.filename, file.mimetype))
  return jsonify({
    'filename': file.filename,
    'mimetype': file.mimetype
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


  
  