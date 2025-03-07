from flask import Flask, render_template,request,jsonify,redirect,url_for,session
import os
import random
import json
from PIL import Image
import requests
from flask import send_from_directory


app = Flask(__name__)
app.secret_key = 'your_secret_key'
# Define the Rapid API key and URL
apiKey = "3b6e3670b5msh1b73bf6ae5604aep1f4348jsnf8b074a57587"
url = "https://try-on-diffusion.p.rapidapi.com/try-on-file"


UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



with open('data.json', 'r') as jf:
    data = json.load(jf)

@app.route('/get_data', methods=['GET'])
def getData():
    try:
        with open('dataset.json', 'r') as file:
            dataset = file.read()
            return jsonify(dataset)
    except FileNotFoundError:
        return jsonify({"error": "Dataset not found"}), 404

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/', methods=['GET', 'POST'])
def login():
  
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        print('user'+email+ "password" +password )

        session['user']=email
        session.permanent = True
        if data['login'].get(email, None) and data['login'][email]==password:
            return redirect(url_for('home'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirmPassword = request.form['confirm-password']

        print('user'+email+ "password" +password +'confirmPassword'+confirmPassword )
        data['login'][email] = password

        with open('data.json', 'w') as f:
            json.dump(data, f)

        session['user']=email
        session.permanent = True

        return redirect(url_for('home'))
    
    return render_template('register.html')



def get_womens_items():

    global womens_images_folder
    womens_images_folder = os.path.join(app.static_folder, 'assets', 'women','tops')

    # Get a list of filenames in the folder
    womens_clothing_images = [file for file in os.listdir(womens_images_folder) if file.endswith(('.jpg', '.png', '.jpeg'))]

    # Create a list of dictionaries with image and random price
    womens_clothing_data = [{'image': file, 'price': random.randint(400, 600)} for file in womens_clothing_images]

    return womens_clothing_data


# @app.route('/women', methods=['GET', 'POST'])
# def women():

#     women_data = get_womens_items()

#     if request.method == 'POST':
#         index = int(request.form.get('index'))
#         uploaded_file = request.files['file']

#         # do processing
#         im = Image.open(os.path.join(womens_images_folder, women_data[index]['image']))
#         im.save('./inputs/cloth.jpg')
#         uploaded_file.save('./inputs/model.jpg')

#         #temp image src , replace with result src
#         image="/static/assets/mens/tshirt-4.png"
#         return jsonify(image)
        

#     return render_template('women.html',women_data=women_data,len=len(women_data))


# Dynamic route for individual product pages
@app.route('/<gender>/<category>/<int:index>', methods=['GET','POST'])
def product_details(gender, category, index):

    print(gender,category,index)
    if request.method == 'POST':
        gender = gender.replace('"','')
        with open('dataset.json', 'r') as file:
            dataset = json.load(file)
            products = dataset.get(gender, {}).get(category, [])

            print(products)
            if 0 <= index < len(products):
                # Retrieve the details of the selected product using the index
                selected_product = products[index]

                # cloth image path
                img = selected_product['img']
                uploaded_img = request.files['file']

                # do processing

                print("Reached Here !")

                #temp image src , replace with result src
                image="/static/assets/mens/shirts/shirt2.png"
                return jsonify(image)
            return jsonify("No products found")
    else:
        print("out of if")
        with open('dataset.json', 'r') as file:
            dataset = json.load(file)
            products = dataset.get(gender, {}).get(category, [])

            if 0 <= index < len(products):
                # Retrieve the details of the selected product using the index
                selected_product = products[index]
                img = selected_product['img'].replace("./static/","")
                return render_template('product_details.html', product=selected_product,gender=gender,img=img,index=index)
            else:
                return render_template('error.html', message=f'Invalid index for {category}')
        

# Assuming cart.json exists and is initially an empty dictionary
cart_data = {}

@app.route('/add_to_cart/<gender>/<category>/<int:index>', methods=['POST'])
def addToCart(gender, category, index):
    try:
        with open('dataset.json', 'r') as file:
            dataset = json.load(file)
            products = dataset.get(gender, {}).get(category, [])

            if 0 <= index < len(products):
                # Retrieve the details of the selected product using the index
                selected_product = products[index]

                user = session.get('user')
                # Construct the key for the user in the cart
                user_key = user + str(request.remote_addr)

                # If the user does not exist in the cart, create an empty list
                if user_key not in cart_data:
                    cart_data[user_key] = []

                # Append the selected product to the user's cart
                cart_data[user_key].append(selected_product)

                # Save the updated cart data to cart.json
                with open('cart.json', 'w') as cart_file:
                    json.dump(cart_data, cart_file, indent=2)

                return jsonify({"message": "Added to Cart"})
            else:
                return jsonify({"error": f'Invalid index for {category}'}), 404
    except FileNotFoundError:
        return jsonify({"error": 'Dataset not found'}), 500




@app.route('/men', methods=['GET','POST'])
def men():
    return render_template('men.html')

@app.route('/women', methods=['GET','POST'])
def women():
    return render_template('women.html')

@app.route('/view-cart', methods=['GET','POST'])
def view_cart():
    if 'user' not in session:
        # If the user is not logged in, redirect them to the login page
        return redirect('/')  # Provide the correct login page URL

    current_user = session['user']
    if request.method == 'GET':
        # Read cart data from cart.json for the current user
        with open('cart.json', 'r') as cart_file:
            cart_data = json.load(cart_file).get(current_user+str(request.remote_addr), [])

        print(cart_data)

        return render_template('view_cart.html', cart_data=cart_data)
    

@app.route('/try_on', methods=['POST'])
def try_on():
    # Ensure the user is logged in
    if 'user' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    # Get the uploaded clothing and avatar images
    clothing_image = request.files['clothing_image']
    avatar_image = request.files['avatar_image']

    # Save the uploaded files temporarily
    clothing_image_path = './uploads/clothing_image.jpg'
    avatar_image_path = './uploads/avatar_image.jpg'
    clothing_image.save(clothing_image_path)
    avatar_image.save(avatar_image_path)

    # Send the images to the third-party API
    url = "https://try-on-diffusion.p.rapidapi.com/try-on-file"
    headers = {
        'x-rapidapi-host': 'try-on-diffusion.p.rapidapi.com',
        'x-rapidapi-key': '3b6e3670b5msh1b73bf6ae5604aep1f4348jsnf8b074a57587'
    }
    files = {
        'clothing_image': open(clothing_image_path, 'rb'),
        'avatar_image': open(avatar_image_path, 'rb')
    }
    response = requests.post(url, headers=headers, files=files)
    
    # Process the response
    if response.status_code == 200:
        with open('./uploads/output_image.png', 'wb') as out_file:
            out_file.write(response.content)
        return jsonify({'image_url': url_for('static', filename='uploads/output_image.png')})
    else:
        return jsonify({'error': 'Error processing images'}), 500
    
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Get the uploaded files from the form
        clothing_image = request.files['clothing_image']
        avatar_image = request.files['avatar_image']

        # Ensure the files exist
        if not clothing_image or not avatar_image:
            return jsonify({"error": "Both clothing and avatar images are required"}), 400

        # Print file details for debugging
        print(f"Clothing Image: {clothing_image.filename}, Size: {clothing_image.content_length}")
        print(f"Avatar Image: {avatar_image.filename}, Size: {avatar_image.content_length}")

        # Prepare files for the API request
        files = {
            'clothing_image': (clothing_image.filename, clothing_image.stream, clothing_image.content_type),
            'avatar_image': (avatar_image.filename, avatar_image.stream, avatar_image.content_type)
        }

        headers = {
            'x-rapidapi-host': 'try-on-diffusion.p.rapidapi.com',
            'x-rapidapi-key': apiKey,
        }

        # Make the API call
        response = requests.post(url, files=files, headers=headers)

        # Handle the response from the API
        if response.status_code == 200:
            # Save the output image directly to the 'uploads' folder
            output_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output_image.png')
            with open(output_image_path, 'wb') as out_file:
                out_file.write(response.content)

            # Return the URL of the output image (serve it from the 'uploads' folder)
            return jsonify({'image_url': f'/uploads/output_image.png'})

        # If the API response is not successful, return an error message
        return jsonify({"error": "Error from RapidAPI: " + response.text}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
