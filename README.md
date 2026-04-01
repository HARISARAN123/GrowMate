# GrowMate

Growmate is an AI-powered farming solution designed to assist farmers in optimizing their agricultural practices. This Flask-based web application integrates advanced features such as plant disease detection and farm management tools to enhance productivity and sustainability.

## Features

- **AI Plant Disease Detection**: Utilizes cutting-edge AI to diagnose plant diseases, preventing crop losses and improving overall farm health.
- **Farm Management**: Optimizes resources—water, soil health, and crop planning—with AI-driven insights for improved productivity and sustainability.
- **AI Farming Assistant**: Provides real-time advice and actionable recommendations, from disease prevention to crop selection, via GrowMate's intelligent AI Assistant.

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/HARISARAN123/GrowMate.git
   cd GrowMate
   ```

2. **Create and activate a virtual environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required packages**:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Copy `.env.example` to `.env` and adjust values for your environment:

```bash
cp .env.example .env
# Windows PowerShell:
Copy-Item .env.example .env
```

Then ensure the following variables are present:

```env
SECRET_KEY=your_secret_key_here
GEMINI_API_KEY=your_gemini_api_key_here
FIREBASE_API_KEY=your_firebase_web_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
FIREBASE_MEASUREMENT_ID=your_measurement_id

# One of the following for Firebase Admin SDK credentials:
FIREBASE_CREDENTIALS_PATH=path_to_service_account_json
# or
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
# or
FIREBASE_SERVICE_ACCOUNT_B64=base64_encoded_service_account_json
```

- **`SECRET_KEY`**: A secret key for Flask session management.
- **`GEMINI_API_KEY`**: Your API key for integrating with the Gemini service.
- **`FIREBASE_*`**: Firebase web config values for login/signup pages.
- **`FIREBASE_CREDENTIALS_PATH` / `FIREBASE_SERVICE_ACCOUNT_JSON` / `FIREBASE_SERVICE_ACCOUNT_B64`**: Firebase Admin credential source.

## Data Storage

- Authentication is handled by Firebase Auth.
- Application data is stored in Firestore:
   - `users/{uid}`
   - `users/{uid}/chat_sessions/{sessionId}/messages/{messageId}`
   - `users/{uid}/analysis_history/{analysisId}`
   - `users/{uid}/farm_recommendations/{recommendationId}`

## Running the Application

Start the Flask development server:

```bash
python app.py
```

The application will be accessible at `http://127.0.0.1:5000/`.

## Usage

- **Plant Disease Detection**: Upload images of your plants to receive AI-driven disease diagnostics.
- **Farm Management**: Access tools for optimizing water usage, monitoring soil health, and planning crop rotations.
- **AI Farming Assistant**: Interact with the chatbot to get real-time farming advice and recommendations.

## Contributing

[Contributions](CONTRIBUTING.md) are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the developers and contributors of the open-source libraries and APIs utilized in this project.
and aqro.in to help developing this project

---

