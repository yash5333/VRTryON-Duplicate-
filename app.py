from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
import os
import json
import random
import base64
import requests
from PIL import Image

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load API key from environment variable
api_key = os.getenv("SG_0094b5ff7fd0e3a9")
url = "https://api.segmind.com/v1/try-on-diffusion"

# Upload folder setup
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load user data
with open('data.json', 'r') as jf:
    data = json.load(jf)

def image_to_base64(image_path):
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    password = request.form['password']
    data['login'][email] = password
    with open('data.json', 'w') as f:
        json.dump(data, f)
    session['user'] = email
    return redirect(url_for('home'))

@app.route('/try_on', methods=['POST'])
def try_on():
    if 'user' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    clothing_image = request.files['clothing_image']
    avatar_image = request.files['avatar_image']

    clothing_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'clothing.jpg')
    avatar_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'avatar.jpg')
    
    clothing_image.save(clothing_image_path)
    avatar_image.save(avatar_image_path)

    data = {
        "model_image": image_to_base64(avatar_image_path),
        "cloth_image": image_to_base64(clothing_image_path),
        "category": "Upper body",
        "num_inference_steps": 35,
        "guidance_scale": 2,
        "seed": 12467,
        "base64": False
    }

    headers = {'x-api-key': api_key, 'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        return jsonify({'image_url': result.get('output_image_url', 'Error: No image returned')})
    return jsonify({'error': 'API request failed'}), response.status_code

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
