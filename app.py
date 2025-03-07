from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
import os
import random
import json
from PIL import Image
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Define the Segmind API key and URL
SEGMIND_API_KEY = "your_segmind_api_key"  # Replace with actual key
SEGMIND_URL = "https://api.segmind.com/tryon"  # Replace with Segmind's API endpoint

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

with open('data.json', 'r') as jf:
    data = json.load(jf)

@app.route('/try_on', methods=['POST'])
def try_on():
    if 'user' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    clothing_image = request.files['clothing_image']
    avatar_image = request.files['avatar_image']

    clothing_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'clothing_image.jpg')
    avatar_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'avatar_image.jpg')
    clothing_image.save(clothing_image_path)
    avatar_image.save(avatar_image_path)

    # Send request to Segmind API
    headers = {
        'Authorization': f'Bearer {SEGMIND_API_KEY}'
    }
    files = {
        'clothing_image': open(clothing_image_path, 'rb'),
        'avatar_image': open(avatar_image_path, 'rb')
    }
    response = requests.post(SEGMIND_URL, headers=headers, files=files)
    
    if response.status_code == 200:
        output_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output_image.png')
        with open(output_image_path, 'wb') as out_file:
            out_file.write(response.content)
        return jsonify({'image_url': url_for('uploaded_file', filename='output_image.png')})
    else:
        return jsonify({'error': 'Error processing images'}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
