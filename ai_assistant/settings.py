INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'agents.apps.AgentsConfig',
    'slack_agent',
    'code_reviewer_agent',
]

# Add at the bottom of the file
from dotenv import load_dotenv
import os
import dj_database_url

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') 
SECRET_KEY='purnam'
SERPER_API_KEY = os.getenv('SERPER_API_KEY')
FINANCIAL_DATASETS_API_KEY = os.getenv('FINANCIAL_DATASETS_API_KEY')
SEARCHAPI_API_KEY = os.getenv('SEARCHAPI_API_KEY')
if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY not found. Please set it in your environment variables or .env file.")

# OpenAI and other API settings


# Document processing settings
MAX_UPLOAD_SIZE = 5242880  # 5MB
ALLOWED_DOCUMENT_TYPES = ['pdf', 'docx', 'png', 'jpg', 'jpeg'] 

# Add these to your existing settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')
STATIC_ROOT = "app-root/repo/wsgi/static"

STATIC_URL = '/static/'

ROOT_URLCONF = 'ai_assistant.urls'
DEBUG = True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.ngrok.io',  # Allow all ngrok subdomains
    'your-ngrok-subdomain.ngrok.io'
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'agents', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Create media directory
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Add these if missing
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   
    'ai_assistant.middleware.FirebaseAuthMiddleware',
]

DATABASES = {
     'default': dj_database_url.config(
        # Replace this value with your local database's connection string.
        default='postgresql://postgres:postgres@localhost:5432/ai_assistant',
        conn_max_age=600
     )
}

LOGIN_URL = '/admin/'  # Since we're using admin login

CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok.io',
    'http://*.ngrok.io',
]

CORS_ALLOWED_ORIGINS = [
    'https://ai-agents-nh6y.onrender.com',
    'https://*.onrender.com',
    'https://www.purnam.ai/',
    'localhost'
]
CORS_ALLOW_CREDENTIALS = True