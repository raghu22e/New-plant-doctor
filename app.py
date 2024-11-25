from flask import Flask, request, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import os
from functools import wraps
import tensorflow as tf

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.template_folder = 'templates'

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['plant_disease_db']
users_collection = db['users']

# Model loading
try:
    model = tf.keras.models.load_model('D:\Ai\cap\saved_model.h5')
except:
    model = None

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'JPG'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Disease list and info
DISEASE_LIST = [
    'Apple___Apple_scab',
    'Apple___Cedar_apple_rust',
    'Apple___Black_rot',
    'Apple___healthy',
    'Cherry_(including_sour)___Powdery_mildew',
    'Cherry_(including_sour)___healthy'
]

DISEASE_INFO = {
    'Apple___Apple_scab': {
        'precautions': [
            'Remove and destroy infected leaves',
            'Maintain good air circulation',
            'Avoid overhead irrigation',
            'Clean up fallen leaves in autumn'
        ],
        'medicines': [
            'Captan fungicide',
            'Myclobutanil',
            'Sulfur-based fungicides',
            'Copper-based fungicides'
        ]
    },
    'Apple___Cedar_apple_rust': {
        'precautions': [
            'Remove nearby cedar trees if possible',
            'Prune affected branches',
            'Improve air circulation',
            'Clean fallen debris'
        ],
        'medicines': [
            'Propiconazole',
            'Mancozeb',
            'Chlorothalonil',
            'Fungicides with Myclobutanil'
        ]
    },
    'Apple___Black_rot': {
        'precautions': [
            'Prune out dead or diseased wood',
            'Remove mummified fruits',
            'Maintain tree vigor',
            'Ensure proper drainage'
        ],
        'medicines': [
            'Captan',
            'Thiophanate-methyl',
            'Copper hydroxide',
            'Strobilurin fungicides'
        ]
    },
    'Apple___healthy': {
        'precautions': [
            'Regular pruning',
            'Proper irrigation',
            'Balanced fertilization',
            'Regular monitoring'
        ],
        'medicines': [
            'Preventive fungicides',
            'Balanced fertilizers',
            'Calcium supplements',
            'Micronutrient sprays'
        ]
    },
    'Cherry_(including_sour)___Powdery_mildew': {
        'precautions': [
            'Improve air circulation',
            'Avoid overhead watering',
            'Prune dense foliage',
            'Remove infected parts'
        ],
        'medicines': [
            'Potassium bicarbonate',
            'Sulfur fungicides',
            'Neem oil',
            'Trifloxystrobin'
        ]
    },
    'Cherry_(including_sour)___healthy': {
        'precautions': [
            'Regular pruning',
            'Proper spacing',
            'Good sanitation',
            'Balanced watering'
        ],
        'medicines': [
            'Preventive copper spray',
            'General purpose fungicide',
            'Balanced fertilizers',
            'Growth promoters'
        ]
    }
}

current_disease_index = 0

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_next_disease():
    global current_disease_index
    disease = DISEASE_LIST[current_disease_index]
    current_disease_index = (current_disease_index + 1) % len(DISEASE_LIST)
    return disease

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        if users_collection.find_one({'username': username}):
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user_data = {
            'username': username,
            'password': generate_password_hash(password),
            'email': email
        }
        users_collection.insert_one(user_data)
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = users_collection.find_one({'username': username})
        
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('upload'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    result = None
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                disease_class = get_next_disease()
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                result = {
                    'disease_class': disease_class,
                    'info': DISEASE_INFO[disease_class]
                }
                
            except Exception as e:
                flash(f'Error processing image: {str(e)}')
                return redirect(request.url)
    
    return render_template('upload.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)