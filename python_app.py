from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from gemini_connection import analyze_image_with_gemini
import json
from dotenv import load_dotenv



app = Flask(__name__)

load_dotenv()

# Configure upload folder
UPLOAD_FOLDER = 'uploads'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

OPEN_AI_KEY = os.getenv("OPENAI_API_KEY")
if not OPEN_AI_KEY:
    raise ValueError("❌ GEMINI API KEY is missing. Please check your .env file.")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def test_route():
    return render_template(
        'index.html',
        title='Gemini Image Analysis'
    )

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
            result = analyze_image_with_gemini(filepath, OPEN_AI_KEY)
            
            if "json" in result:
                json_part = result.split("{", 1)[1].rsplit("}", 1)[0]
                try:
                    dict_values = json.loads("{" + json_part + "}")
                    response = jsonify(dict_values)

                    # Add CORS headers
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 200
                except json.JSONDecodeError as e:
                    return jsonify({'error': 'Failed to parse analysis results'}), 500
            else:
                return jsonify({'error': 'Invalid response format from analysis'}), 500

        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
    
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)