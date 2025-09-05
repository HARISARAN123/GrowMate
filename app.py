import os
import logging
import requests
import markdown
import functools  # Add this line
from flask import Flask, render_template,send_from_directory, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from disease_detection import analyze_plant_disease, get_gemini_analysis, fetch_gemini_response

# Load environment variables
load_dotenv()


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file upload size to 16MB


# Initialize Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, auth
if not firebase_admin._apps:
    try:
        cred_path = os.path.join(os.path.dirname(__file__), "aqro-f0322-firebase-adminsdk-fbsvc-f82124232c.json")
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            print(f"✅ Firebase credentials found at: {cred_path}")
        else:
            cred = credentials.Certificate("aqro-f0322-firebase-adminsdk-fbsvc-f82124232c.json")
            print("✅ Using direct path for Firebase credentials")
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully")
        print(f"✅ Project ID: {cred.project_id}")
    except Exception as e:
        print(f"❌ Failed to initialize Firebase: {e}")
        print(f"❌ Current directory: {os.getcwd()}")
        print(f"❌ Files in directory: {os.listdir('.')}")
        raise

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Utility function to create unique filenames for uploads
def make_unique_filename(filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    unique_filename = filename
    while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)):
        unique_filename = f"{base}_{counter}{ext}"
        counter += 1
    return unique_filename


# Login route using Firebase Authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login with Firebase ID token."""
    if request.method == 'POST':
        id_token = request.form.get('idToken')
        if not id_token:
            flash('No authentication token provided.', 'error')
            return redirect(url_for('login'))
        
        try:
            # Verify the Firebase ID token
            decoded_token = auth.verify_id_token(id_token)
            session['logged_in'] = True
            session['email'] = decoded_token.get('email', '')
            session['uid'] = decoded_token.get('uid', '')
            session['name'] = decoded_token.get('name', '')
            flash('Login successful!', 'success')
            
            # Redirect to the page user was trying to access, or home
            next_page = request.form.get('next') or url_for('home')
            return redirect(next_page)
            
        except ValueError as ve:
            logger.error(f"Invalid token format: {ve}")
            flash('Invalid authentication token format.', 'error')
        except auth.InvalidIdTokenError as ie:
            logger.error(f"Invalid ID token: {ie}")
            flash('Authentication token is invalid or expired.', 'error')
        except auth.ExpiredIdTokenError as ee:
            logger.error(f"Expired token: {ee}")
            flash('Authentication token has expired. Please log in again.', 'error')
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            flash('Authentication failed. Please try again.', 'error')
    
    return render_template(
        'login.html',
        firebase_api_key=os.getenv('FIREBASE_API_KEY'),
        firebase_auth_domain=os.getenv('FIREBASE_AUTH_DOMAIN'),
        firebase_project_id=os.getenv('FIREBASE_PROJECT_ID'),
        firebase_storage_bucket=os.getenv('FIREBASE_STORAGE_BUCKET'),
        firebase_messaging_sender_id=os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
        firebase_app_id=os.getenv('FIREBASE_APP_ID'),
        firebase_measurement_id=os.getenv('FIREBASE_MEASUREMENT_ID')
    )

# Signup route (handled on frontend)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration with Firebase (handled on frontend)."""
    # Registration is handled by Firebase on the frontend.
    # Optionally, you can collect extra user info here if needed.
    return render_template(
        'signup.html',
        firebase_api_key=os.getenv('FIREBASE_API_KEY'),
        firebase_auth_domain=os.getenv('FIREBASE_AUTH_DOMAIN'),
        firebase_project_id=os.getenv('FIREBASE_PROJECT_ID'),
        firebase_storage_bucket=os.getenv('FIREBASE_STORAGE_BUCKET'),
        firebase_messaging_sender_id=os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
        firebase_app_id=os.getenv('FIREBASE_APP_ID'),
        firebase_measurement_id=os.getenv('FIREBASE_MEASUREMENT_ID')
    )

# Logout route
@app.route('/logout')
def logout():
    """Handle user logout."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home'))

# Add a decorator to protect routes that require login
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in') or not session.get('uid'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

# Test route to verify Firebase authentication
@app.route('/test-auth')
def test_auth():
    """Test route to verify Firebase is working"""
    try:
        # Test if Firebase is initialized
        app_info = firebase_admin.get_app()
        return jsonify({
            'status': 'success',
            'message': 'Firebase is initialized correctly',
            'project_id': app_info.project_id if hasattr(app_info, 'project_id') else 'N/A'
        })
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': f'Firebase error: {str(e)}'
        }), 500
@app.route('/disease-detection', methods=['GET', 'POST'])
@login_required
def disease_detection():
    if request.method == 'POST':
        file = request.files.get('image')
        if not file or file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        filename = secure_filename(file.filename)
        filename = make_unique_filename(filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        try:
            result = analyze_plant_disease(file_path)  # Analyze disease from the uploaded image
            gemini_analysis = get_gemini_analysis(result['prediction'], result['confidence'])  # Get Gemini analysis
        except Exception as e:
            logger.error(f"Error analyzing plant disease: {e}")
            flash('Error analyzing plant disease')
            return redirect(request.url)
        image_url = url_for('static', filename=f'uploads/{filename}')
        logger.info(f"Result: {result}")
        logger.info(f"Gemini Analysis: {gemini_analysis}")
        gemini_analysis_html = markdown.markdown(gemini_analysis)
        return render_template('result.html', result=result, gemini_analysis=gemini_analysis_html, image_url=image_url)
    return render_template('disease_detection.html')


@app.route('/farm-management', methods=['GET', 'POST'])
@login_required
def farm_management():
    """Handle farm management recommendations."""
    if request.method == 'POST':
        area = request.form.get('area')
        Soil_test_result = request.form.get('Soil_test_result')
        location = request.form.get('location')
        language = request.form.get('language')
        recommendation = get_farm_recommendations(area, Soil_test_result, language, location)
        # Convert recommendation to HTML using markdown
        recommendation_html = markdown.markdown(recommendation)

        return render_template('farm_management.html', recommendation=recommendation_html)
    return render_template('farm_management.html')


def get_farm_recommendations(area, Soil_test_result, language, location):
    """Get farm recommendations using the Gemini API."""
    prompt = (
        f"Provide farm management recommendations for an area of {area} in acre, "
        f"with {Soil_test_result} Soil Test result, located in {location}. "
        f"Include crop suggestions and basic care instructions. Reply in {language} "
        f"with all new features. Also, provide important points and methods of "
        f"division of crops. Always reply like you're a bot called Growmate."
    )

    return fetch_gemini_response(prompt)



@app.route('/chatbot', methods=['GET', 'POST'])
@login_required
def chatbot():
    """Handle chatbot interactions."""
    if 'chat_history' not in session:
        session['chat_history'] = []  # Initialize chat history
    if request.method == 'POST':
        message = request.form['message']
        raw_response = get_gemini_reply(message)
        # Convert raw response to HTML using markdown
        formatted_response = markdown.markdown(raw_response)
        session['chat_history'].append(("You", message))
        session['chat_history'].append(("Bot", formatted_response))  # Use the formatted response
        return jsonify({"response": formatted_response})
    return render_template('chatbot.html', chat_history=session['chat_history'])


def get_gemini_reply(message):
    """Get chatbot reply using the Gemini API."""
    return fetch_gemini_response(message)


def fetch_gemini_response(prompt):
    """Fetch response from Gemini API."""
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # Store the API key securely
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        logger.info(f"Gemini analysis response data: {response_data}")
        if 'candidates' in response_data and response_data['candidates']:
            candidate = response_data['candidates'][0]
            text_part = candidate.get('content', {}).get('parts', [{}])[0]
            return text_part.get('text', "Unable to fetch detailed analysis.")
        else:
            logger.warning("No candidates found in response.")
            return "Unable to generate analysis at this time."
    except requests.RequestException as e:
        logger.error(f"Error fetching Gemini analysis: {e}")
        return "Error occurred while fetching analysis."


@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    file = request.files.get('image')
    if not file or file.filename == '':
        return jsonify({'error': 'No file provided'}), 400
    filename = secure_filename(file.filename)
    filename = make_unique_filename(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    try:
        result = analyze_plant_disease(file_path)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error analyzing plant disease: {e}")
        return jsonify({'error': 'Failed to analyze disease'}), 500


@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/robots.txt')
def robots():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'Robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'sitemap.xml')

# Custom 500 error handler
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html'), 500

@app.errorhandler(404)
def page_not_found(e):
    # Render the custom 404 page
    return render_template('error.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)
