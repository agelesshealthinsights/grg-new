from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from gemini_connection import analyze_image_with_gemini
import json
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

load_dotenv()

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Changed to correct environment variable
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI API KEY is missing. Please check your .env file.")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Add root route
@app.route('/')
def index():
    return render_template('index.html')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/analyze_image', methods=['POST', 'OPTIONS'])
def analyze_image():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        return response

    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        
        try:
            result = analyze_image_with_gemini(filepath, GEMINI_API_KEY)
            
            # Try to find JSON content in the response
            try:
                # First try to parse the entire response as JSON
                dict_values = json.loads(result)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the text
                try:
                    if "{" in result and "}" in result:
                        json_part = result.split("{", 1)[1].rsplit("}", 1)[0]
                        dict_values = json.loads("{" + json_part + "}")
                    else:
                        # If no JSON found, return the raw text
                        dict_values = {"text": result}
                except json.JSONDecodeError:
                    dict_values = {"text": result}
            
            response = jsonify(dict_values)
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 200

        except Exception as e:
            app.logger.error(f"Error processing image: {str(e)}")
            return jsonify({'error': f'Error processing image: {str(e)}'}), 500
        
        finally:
            # Clean up the uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
    
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
