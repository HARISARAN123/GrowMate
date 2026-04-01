import os
import json
import base64
import uuid
import re
import logging
import markdown
import functools
from flask import Flask, render_template,send_from_directory, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from disease_detection import analyze_plant_disease, get_gemini_analysis, fetch_gemini_response
from firebase_service import (
    upsert_user_profile,
    save_disease_analysis,
    save_farm_recommendation,
    save_chat_message,
    get_chat_messages,
    create_chat_session,
)

# Load environment variables
load_dotenv(override=True)


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file upload size to 16MB


# Initialize Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin import firestore


def firebase_project_mismatch_message():
    """Return a mismatch message if web/app Firebase projects differ."""
    expected_project_id = (os.getenv('FIREBASE_PROJECT_ID') or '').strip()
    admin_project_id = ''
    try:
        admin_project_id = (firebase_admin.get_app().project_id or '').strip()
    except Exception:
        return None

    if expected_project_id and admin_project_id and expected_project_id != admin_project_id:
        return (
            f"Firebase project mismatch: web config uses '{expected_project_id}' "
            f"but Admin SDK uses '{admin_project_id}'. Update FIREBASE_CREDENTIALS_PATH "
            "or FIREBASE_SERVICE_ACCOUNT_JSON/B64 to a service account from the same project."
        )
    return None


def initialize_firebase():
    """Initialize Firebase app from env or local credential file."""
    if firebase_admin._apps:
        return firebase_admin.get_app()

    service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
    service_account_b64 = os.getenv('FIREBASE_SERVICE_ACCOUNT_B64')
    service_account_path = os.getenv(
        'FIREBASE_CREDENTIALS_PATH',
        os.path.join(os.path.dirname(__file__), 'aqro-f0322-firebase-adminsdk-fbsvc-f82124232c.json'),
    )

    try:
        if service_account_json:
            cred = credentials.Certificate(json.loads(service_account_json))
        elif service_account_b64:
            decoded = base64.b64decode(service_account_b64).decode('utf-8')
            cred = credentials.Certificate(json.loads(decoded))
        elif os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
        else:
            raise RuntimeError('Firebase credentials not found. Set FIREBASE_SERVICE_ACCOUNT_JSON, FIREBASE_SERVICE_ACCOUNT_B64, or FIREBASE_CREDENTIALS_PATH.')

        return firebase_admin.initialize_app(cred)
    except Exception as e:
        logger.error("Failed to initialize Firebase: %s", e)
        raise

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

initialize_firebase()

mismatch_message = firebase_project_mismatch_message()
if mismatch_message:
    logger.warning(mismatch_message)

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


def render_ai_markdown(text):
    """Render AI markdown with richer formatting support (tables, lists, code)."""
    return markdown.markdown(
        text or "",
        extensions=['extra', 'sane_lists', 'nl2br'],
        output_format='html5',
    )


def get_firebase_template_context():
    """Return Firebase web config for auth templates."""
    def clean_value(name):
        raw = (os.getenv(name) or '').strip().strip('"').strip("'")
        if not raw:
            return ''
        # Keep only the first token if accidental pasted text exists.
        return raw.split()[0].rstrip(',;')

    raw_api_key = (os.getenv('FIREBASE_API_KEY') or '').strip()
    api_key_match = re.search(r'(AIza[0-9A-Za-z_-]{20,})', raw_api_key)
    firebase_api_key = api_key_match.group(1) if api_key_match else clean_value('FIREBASE_API_KEY')

    return {
        'firebase_api_key': firebase_api_key,
        'firebase_auth_domain': clean_value('FIREBASE_AUTH_DOMAIN'),
        'firebase_project_id': clean_value('FIREBASE_PROJECT_ID'),
        'firebase_storage_bucket': clean_value('FIREBASE_STORAGE_BUCKET'),
        'firebase_messaging_sender_id': clean_value('FIREBASE_MESSAGING_SENDER_ID'),
        'firebase_app_id': clean_value('FIREBASE_APP_ID'),
        'firebase_measurement_id': clean_value('FIREBASE_MEASUREMENT_ID'),
    }


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
            uid = decoded_token.get('uid', '')
            email = decoded_token.get('email', '')
            name = decoded_token.get('name', '')

            session['logged_in'] = True
            session['email'] = email
            session['uid'] = uid
            session['name'] = name

            upsert_user_profile(
                uid,
                {
                    'uid': uid,
                    'email': email,
                    'name': name,
                    'auth_provider': decoded_token.get('firebase', {}).get('sign_in_provider', ''),
                },
            )

            flash('Login successful!', 'success')
            
            # Redirect to the page user was trying to access, or home
            next_page = request.form.get('next') or url_for('home')
            return redirect(next_page)
            
        except ValueError as ve:
            logger.error(f"Invalid token format: {ve}")
            flash('Invalid authentication token format.', 'error')
        except auth.InvalidIdTokenError as ie:
            logger.error(f"Invalid ID token: {ie}")
            mismatch_message = firebase_project_mismatch_message()
            if mismatch_message:
                flash(mismatch_message, 'error')
            else:
                flash('Authentication token is invalid or expired.', 'error')
        except auth.ExpiredIdTokenError as ee:
            logger.error(f"Expired token: {ee}")
            flash('Authentication token has expired. Please log in again.', 'error')
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            flash('Authentication failed. Please try again.', 'error')
    
    return render_template('login.html', **get_firebase_template_context())

# Signup route (handled on frontend)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration and profile persistence with Firebase + Firestore."""
    if request.method == 'POST':
        id_token = request.form.get('idToken')
        if not id_token:
            flash('No authentication token provided.', 'error')
            return redirect(url_for('signup'))

        try:
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token.get('uid', '')
            email = decoded_token.get('email', request.form.get('email', ''))
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            user_type = request.form.get('user_type', '').strip()
            farm_location = request.form.get('farm_location', '').strip()
            full_name = (f"{first_name} {last_name}").strip() or decoded_token.get('name', '')

            upsert_user_profile(
                uid,
                {
                    'uid': uid,
                    'email': email,
                    'name': full_name,
                    'first_name': first_name,
                    'last_name': last_name,
                    'user_type': user_type,
                    'farm_location': farm_location,
                    'auth_provider': decoded_token.get('firebase', {}).get('sign_in_provider', ''),
                    'created_at': firestore.SERVER_TIMESTAMP,
                },
            )

            session['logged_in'] = True
            session['email'] = email
            session['uid'] = uid
            session['name'] = full_name
            flash('Account created successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            logger.error("Signup failed: %s", e)
            flash('Signup failed. Please try again.', 'error')

    return render_template('signup.html', **get_firebase_template_context())

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

        save_disease_analysis(
            session['uid'],
            {
                'image_url': image_url,
                'prediction': result.get('prediction', ''),
                'confidence': float(result.get('confidence', 0.0)),
                'gemini_analysis': gemini_analysis,
            },
        )

        gemini_analysis_html = render_ai_markdown(gemini_analysis)
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
        save_farm_recommendation(
            session['uid'],
            {
                'area': area,
                'soil_test_result': Soil_test_result,
                'language': language,
                'location': location,
                'recommendation': recommendation,
            },
        )
        # Convert recommendation to HTML using markdown
        recommendation_html = render_ai_markdown(recommendation)

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
    uid = session['uid']
    chat_session_id = session.get('chat_session_id')
    if not chat_session_id:
        chat_session_id = str(uuid.uuid4())
        session['chat_session_id'] = chat_session_id
        create_chat_session(uid, chat_session_id)

    if request.method == 'POST':
        message = request.form['message']
        save_chat_message(uid, chat_session_id, 'user', message)

        raw_response, gemini_debug = get_gemini_reply(message, include_debug=True)
        save_chat_message(uid, chat_session_id, 'bot', raw_response)

        return jsonify({"response": raw_response, "debug": gemini_debug})

    return render_template(
        'chatbot.html',
        chat_history=get_chat_messages(uid, chat_session_id),
    )


def get_gemini_reply(message, include_debug=False):
    """Get chatbot reply using the Gemini API."""
    return fetch_gemini_response(message, include_debug=include_debug)


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
        save_disease_analysis(
            session['uid'],
            {
                'image_url': url_for('static', filename=f'uploads/{filename}'),
                'prediction': result.get('prediction', ''),
                'confidence': float(result.get('confidence', 0.0)),
                'source': 'analyze-api',
            },
        )
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