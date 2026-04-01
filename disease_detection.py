import os
import logging
import requests
import time
import json
import re
from typing import Optional
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np

try:
    from google import genai
except Exception:
    genai = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load your pre-trained model
MODEL_PATH = 'plant_model_v5-beta.h5'  # Replace with your actual model path
model = load_model(MODEL_PATH)

# Load class indices from JSON file
def load_class_indices(json_file):
    """Load class indices from a JSON file."""
    with open(json_file, 'r') as file:
        return json.load(file)

class_indices = load_class_indices('class_indices.json')

def analyze_plant_disease(image_path):
    
    """Analyze the plant disease based on the uploaded image."""
    try:
        # Preprocess the image
        img = Image.open(image_path)
        img = img.resize((224, 224))  # Adjust size based on your model
        img_array = np.array(img) / 255.0  # Normalize the image
        img_array = np.expand_dims(img_array, axis=0)

        # Make prediction
        predictions = model.predict(img_array)
        predicted_class_index = np.argmax(predictions, axis=1)[0]
        confidence = np.max(predictions) * 100

        # Map predicted class to label
        predicted_class = class_indices.get(str(predicted_class_index), "Unknown")
        result = {
            'prediction': predicted_class,
            'confidence': confidence,
        }
        logger.info(f"Prediction: {result['prediction']} with confidence: {result['confidence']:.2f}%")
        return result
    except Exception as e:
        logger.error(f"Error analyzing plant disease: {e}")
        raise

def get_gemini_analysis(prediction, confidence):
    """Get Gemini analysis based on prediction and confidence."""
    prompt = (f"Provide a detailed analysis of the plant disease prediction: '{prediction}' with a confidence of {confidence:.2f}%. "
            f"Ensure the response includes care tips and specific recommendations. "
            "If the prediction seems incomplete or unclear, Just tell Retry")

    response = fetch_gemini_response(prompt)
    return response

def fetch_gemini_response(prompt, include_debug=False):
    """Fetch response from Gemini API.

    If include_debug=True, returns (text_response, debug_info).
    """
    def normalize_model_name(model_name):
        if not model_name:
            return ''
        cleaned = model_name.strip()
        if cleaned.startswith('models/'):
            cleaned = cleaned.split('models/', 1)[1]
        return cleaned

    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    primary_model = normalize_model_name(os.getenv('GEMINI_MODEL', 'gemini-3-flash-preview'))
    fallback_model = normalize_model_name(os.getenv('GEMINI_FALLBACK_MODEL', 'gemini-2.0-flash'))
    model_order = [primary_model]
    if fallback_model and fallback_model not in model_order:
        model_order.append(fallback_model)

    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    sdk_client = genai.Client(api_key=GEMINI_API_KEY) if genai and GEMINI_API_KEY else None

    debug_info = {
        "model": primary_model,
        "models_tried": [],
        "has_api_key": bool(GEMINI_API_KEY),
        "sdk_available": bool(genai),
        "ok": False,
    }

    if not GEMINI_API_KEY:
        message = "Gemini API key is missing. Set GEMINI_API_KEY in environment."
        logger.error(message)
        if include_debug:
            debug_info["error"] = message
            return message, debug_info
        return message

    last_error = None

    def _extract_text_from_sdk_response(sdk_response) -> Optional[str]:
        text = getattr(sdk_response, 'text', None)
        if text:
            return text
        return None

    for model_name in model_order:
        debug_info["models_tried"].append(model_name)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"

        for attempt in range(2):
            # 1) Official Gemini SDK path (preferred).
            if sdk_client:
                try:
                    sdk_response = sdk_client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    text = _extract_text_from_sdk_response(sdk_response)
                    if text:
                        debug_info["ok"] = True
                        debug_info["model"] = model_name
                        debug_info["transport"] = "google-genai-sdk"
                        debug_info["response_length"] = len(text)
                        if include_debug:
                            return text, debug_info
                        return text

                    logger.warning("Gemini SDK response did not include text for model %s.", model_name)
                    last_error = "No text found in Gemini SDK response"
                except Exception as sdk_error:
                    last_error = str(sdk_error)
                    debug_info["sdk_error"] = str(sdk_error)

            try:
                response = requests.post(url, headers=headers, json=data, timeout=45)
                debug_info["http_status"] = response.status_code
                response.raise_for_status()
                response_data = response.json()

                if 'candidates' in response_data and response_data['candidates']:
                    candidate = response_data['candidates'][0]
                    text = candidate.get('content', {}).get('parts', [{}])[0].get('text', "Unable to fetch analysis.")
                    debug_info["ok"] = True
                    debug_info["model"] = model_name
                    debug_info["transport"] = "rest-v1beta"
                    debug_info["response_length"] = len(text)
                    if include_debug:
                        return text, debug_info
                    return text

                logger.warning("Gemini response did not contain candidates for model %s. Response keys: %s", model_name, list(response_data.keys()))
                last_error = "No candidates found in Gemini response"
                break
            except requests.RequestException as e:
                last_error = str(e)
                status_code = e.response.status_code if e.response is not None else None
                if e.response is not None:
                    debug_info["http_status"] = status_code
                    debug_info["response_body"] = e.response.text[:500]

                # Retry once on transient service issues.
                if status_code in (429, 500, 502, 503, 504) and attempt == 0:
                    time.sleep(1.0)
                    continue
                break

    debug_info["error"] = last_error or "Unknown Gemini error"
    logger.error("Error fetching Gemini analysis. Debug: %s", debug_info)

    http_status = debug_info.get("http_status")
    api_message = ""
    if debug_info.get("response_body"):
        try:
            parsed = json.loads(debug_info["response_body"])
            api_message = parsed.get("error", {}).get("message", "")
        except Exception:
            api_message = ""

    tried = ", ".join(debug_info.get("models_tried", []))

    retry_seconds = None
    retry_match = re.search(r"retry in\s+([0-9]+(?:\.[0-9]+)?)s", f"{api_message} {debug_info.get('sdk_error', '')}", re.IGNORECASE)
    if retry_match:
        try:
            retry_seconds = int(float(retry_match.group(1)))
        except Exception:
            retry_seconds = None

    quota_zero = "limit: 0" in f"{api_message} {debug_info.get('sdk_error', '')}".lower()
    billing_hint = "plan and billing" in f"{api_message} {debug_info.get('sdk_error', '')}".lower()

    if http_status == 503:
        message = f"Gemini is currently busy (503). Please retry in a few seconds. Models tried: {tried}."
    elif http_status == 429:
        if quota_zero or billing_hint:
            wait_hint = f" Retry after about {retry_seconds}s." if retry_seconds else ""
            message = (
                "Gemini quota is exhausted for this project (429). "
                "Enable billing or increase Gemini API quota in Google AI Studio/Google Cloud."
                f"{wait_hint} Models tried: {tried}."
            )
        else:
            wait_hint = f" Retry after about {retry_seconds}s." if retry_seconds else ""
            message = f"Gemini rate limit reached (429). Please wait and retry.{wait_hint} Models tried: {tried}."
    elif http_status:
        detail = f" {api_message}" if api_message else ""
        message = f"Gemini API request failed ({http_status}).{detail} Models tried: {tried}."
    else:
        message = f"Unable to fetch AI analysis right now. Models tried: {tried}."

    if include_debug:
        return message, debug_info
    return message