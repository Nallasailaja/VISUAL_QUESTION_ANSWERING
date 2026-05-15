"""
Visual Question Answering (VQA) Flask Application
Allows users to upload images and ask questions about them
"""

import os
import torch
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
from model import load_model, get_model
import time

# Flask Configuration
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif', 'bmp'}
app.config['IMAGE_MAX_WIDTH'] = 800  # Medium image width
app.config['IMAGE_MAX_HEIGHT'] = 600  # Medium image height

# Global model
vqa_model = None


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def init_model():
    """Initialize the VQA model on app startup"""
    global vqa_model
    print("Initializing VQA Model...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    vqa_model = load_model(device=device)
    print("VQA Model initialized successfully!")


@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    """
    API endpoint to predict answer for a question about an image
    
    Expected POST data:
        - image: Image file
        - question: Text question about the image
        
    Returns:
        JSON with answer and status
    """
    try:
        # Check if image file exists
        if 'image' not in request.files:
            return jsonify({'status': 'error', 'answer': 'No image provided'}), 400
        
        file = request.files['image']
        question = request.form.get('question', '').strip()
        
        # Check if file and question are not empty
        if file.filename == '':
            return jsonify({'status': 'error', 'answer': 'No image selected'}), 400
        
        if not question:
            return jsonify({'status': 'error', 'answer': 'No question provided'}), 400
        
        # Check if file is allowed
        if not allowed_file(file.filename):
            return jsonify({'status': 'error', 'answer': 'Invalid file format. Allowed: JPG, PNG, GIF, BMP'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = str(int(time.time()))
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Resize image to medium size
        try:
            image = Image.open(filepath)
            image.thumbnail((app.config['IMAGE_MAX_WIDTH'], app.config['IMAGE_MAX_HEIGHT']), Image.Resampling.LANCZOS)
            image.save(filepath, quality=85, optimize=True)
        except Exception as resize_error:
            print(f"Image resizing warning: {resize_error}")
        
        # Get the model
        model = get_model()
        
        # Generate answer
        answer = model.predict_answer(filepath, question)
        
        # Clean up - delete uploaded file
        try:
            os.remove(filepath)
        except:
            pass
        
        return jsonify({'status': 'success', 'answer': answer, 'question': question}), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'answer': f'Error: {str(e)}'}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'model_loaded': vqa_model is not None}), 200


if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize model
    init_model()
    
    # Run Flask app
    print("Starting VQA Flask Application...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
