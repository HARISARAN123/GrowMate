# GrowMate

Growmate is an AI-powered farming solution designed to assist farmers in optimizing their agricultural practices. This Flask-based web application integrates advanced features such as plant disease detection and farm management tools to enhance productivity and sustainability. ([growmate.tech](https://growmate.tech/?utm_source=chatgpt.com))

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

Create a `.env` file in the root directory to store your environment variables:

```env
SECRET_KEY=your_secret_key_here
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/your_database_name
```

- **`SECRET_KEY`**: A secret key for Flask session management.
- **`GEMINI_API_KEY`**: Your API key for integrating with the Gemini service.
- **`DATABASE_URL`**: The connection URL for your PostgreSQL database.

## Database Initialization

Initialize the database by running:

```bash
python database_init.py
```

This script will set up the necessary tables and schemas in your PostgreSQL database.

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

Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the developers and contributors of the open-source libraries and APIs utilized in this project.
and sparkworks to help to help developing this project

---

For more information, visit our website: [growmate.tech](https://growmate.tech/)
<a href="https://www.digitalocean.com/?refcode=218925646640&utm_campaign=Referral_Invite&utm_medium=Referral_Program&utm_source=badge"><img src="https://web-platforms.sfo2.cdn.digitaloceanspaces.com/WWW/Badge%201.svg" alt="DigitalOcean Referral Badge" /></a>
