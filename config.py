import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    FAL_KEY = os.environ.get('FAL_KEY')
    AVAILABLE_MODELS = {
        "gemini-2.5-flash-image": "gemini-2.5-flash-image",
        "qwen-image-edit-lora": "fal-ai/fast-svd/lcm" 
    }
