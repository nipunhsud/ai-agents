INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'corsheaders',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'agents.apps.AgentsConfig',
    'slack_agent',
    'code_reviewer_agent',
    'help_desk_agent',
    "django_extensions",
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
DEBUG = False

ALLOWED_HOSTS = ['ai-agents-nh6y.onrender.com', 'localhost', '127.0.0.1']


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'chat', 'templates'),
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
    'corsheaders.middleware.CorsMiddleware',
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

LOGIN_URL = '/admin/login/'  # Since we're using admin login

CSRF_TRUSTED_ORIGINS = [
    'https://ai-agents-nh6y.onrender.com', 
    'https://www.purnam.ai/',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

CORS_ALLOWED_ORIGINS = [
    'https://ai-agents-nh6y.onrender.com',
    'https://*.onrender.com',
    'https://www.purnam.ai',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

CORS_ALLOW_CREDENTIALS = True


CSRF_COOKIE_NAME = 'csrftoken'
CSRF_COOKIE_HTTPONLY = False  # Must be False to allow JavaScript to read the token
SESSION_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SAMESITE = 'None'

CSRF_USE_SESSIONS = False
CSRF_COOKIE_DOMAIN = None
CORS_ALLOW_CREDENTIALS = True
CSRF_COOKIE_SECURE = True 
SESSION_COOKIE_SECURE = True    


FIREBASE_CREDENTIALS = os.getenv('FIREBASE_CREDENTIALS')
if FIREBASE_CREDENTIALS:
    import json
    import tempfile
    cred_temp = tempfile.NamedTemporaryFile(delete=False)
    cred_temp.write(FIREBASE_CREDENTIALS.encode())
    cred_temp.close()
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_temp.name