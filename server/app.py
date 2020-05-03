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
    return errormessage('No file part in the request', 400)
  
  file = request.files['file']
  if file.filename == '':
    return errormessage('No file selected for uploading', 400) 


  if not isaudio(file):
    return errormessage('not audio', 400)
  
  # process file
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


  
  