from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='../build')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
CORS(app)

##
# API routes
##

@app.route('/api/items')
def items():
  '''Sample API route for data'''
  return jsonify([{'title': 'A'}, {'title': 'B'}])

##
# View route
##

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
  '''Return index.html for all non-api routes'''
  #pylint: disable=unused-argument
  return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/upload', methods=['POST'])
def upload():
  
  if 'file' not in request.files:
    resp = jsonify({'message': 'No file part in the request'})
    resp.status_code = 400
    return resp
  
  file = request.files['file']
  if file.filename == '':
    resp = jsonify({'message': 'No file selected for uploading'})
    resp.status_code = 400
    return resp 

  
  # process file
  return jsonify({
    'filename': file.filename,
    'mimetype': file.mimetype
  })
  
  