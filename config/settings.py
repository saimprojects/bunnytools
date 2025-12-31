from __future__ import annotations

import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

import cloudinary
import cloudinary.uploader
import cloudinary.api
import dj_database_url
from dotenv import load_dotenv

# Load .env file - explicitly from project root
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'

print(f"🔍 Looking for .env file at: {env_path}")

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print("✅ .env file loaded successfully")
else:
    print("⚠️  WARNING: .env file not found at expected location!")
    # Try to load from current directory as fallback
    load_dotenv()
    print("🔄 Trying to load .env from default locations...")

# SECURITY
SECRET_KEY: str = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured('DJANGO_SECRET_KEY is not set in environment variables')

DEBUG: bool = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

# ALLOWED_HOSTS - Railway ke liye update karo
ALLOWED_HOSTS: list[str] = []

# Environment se ALLOWED_HOSTS lelo
env_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
if env_hosts:
    ALLOWED_HOSTS.extend(env_hosts.split(','))

# Railway domains automatically add karo
ALLOWED_HOSTS.extend([
    '.railway.app',  # Sab railway subdomains allow karega
    'localhost',
    '127.0.0.1',
    '[::1]',
])

# Remove any empty strings
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS if host.strip()]

print(f"🌐 ALLOWED_HOSTS: {ALLOWED_HOSTS}")

# DATABASE - Railway PostgreSQL ONLY
DATABASE_URL: str = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    raise ImproperlyConfigured(
        'DATABASE_URL environment variable is not set.\n'
        'Please add DATABASE_URL to your .env file with Railway PostgreSQL connection string.\n'
        f'Current .env path: {env_path}'
    )

print(f"📊 DATABASE_URL found: {DATABASE_URL[:50]}...")  # Show first 50 chars

# Parse DATABASE_URL
try:
    db_config = dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
    
    # Verify it's PostgreSQL
    engine = db_config.get('ENGINE', '')
    if 'postgresql' not in engine and 'postgres' not in engine:
        raise ImproperlyConfigured(
            f'Database ENGINE should be PostgreSQL, but got: {engine}\n'
            f'Please use a PostgreSQL database from Railway.'
        )
    
    DATABASES = {
        'default': db_config
    }
    
    print(f"✅ Database configured successfully")
    print(f"   Engine: {db_config.get('ENGINE')}")
    print(f"   Name: {db_config.get('NAME')}")
    print(f"   Host: {db_config.get('HOST')}")
    print(f"   Port: {db_config.get('PORT')}")
    
except Exception as e:
    raise ImproperlyConfigured(
        f'Failed to parse DATABASE_URL: {str(e)}\n'
        f'DATABASE_URL value: {DATABASE_URL[:100]}...'
    )

# APPLICATIONS
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'ckeditor',
    'ckeditor_uploader',
    'cloudinary',
    'cloudinary_storage',

    'product',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ✅ SecurityMiddleware ke baad hona chahiye
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# PASSWORD VALIDATORS
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# INTERNATIONALIZATION
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Karachi'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# STATIC FILES
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# MEDIA / CLOUDINARY
MEDIA_URL = '/media/'
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Cloudinary Configuration
CLOUD_NAME = os.environ.get('CLOUD_NAME')
API_KEY = os.environ.get('API_KEY')
API_SECRET = os.environ.get('API_SECRET')

if not all([CLOUD_NAME, API_KEY, API_SECRET]):
    print("⚠️  WARNING: Cloudinary credentials not fully set in .env file")

cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET,
)

# REST FRAMEWORK
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework_simplejwt.authentication.JWTAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticatedOrReadOnly'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

# JWT
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# JAZZMIN
JAZZMIN_SETTINGS = {
    'site_title': 'Administration',
    'site_header': 'Administration',
    'site_brand': 'Admin',
    'welcome_sign': 'Welcome to Admin Panel',
    'show_sidebar': True,
    'navigation_expanded': False,
}

# CKEditor basic config

CKEDITOR_UPLOAD_PATH = "ckeditor_uploads/"

CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": [
            ["Bold", "Italic", "Underline"],
            ["NumberedList", "BulletedList"],
            ["Link", "Unlink"],
            ["RemoveFormat"],
        ],
        "height": 200,
        "width": "auto",
    }
}

# CORS
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:5173').split(',')
CORS_ALLOW_CREDENTIALS = True

# CSRF TRUSTED ORIGINS
CSRF_TRUSTED_ORIGINS = []
if os.environ.get('RAILWAY_PUBLIC_DOMAIN'):
    CSRF_TRUSTED_ORIGINS.append(f"https://{os.environ.get('RAILWAY_PUBLIC_DOMAIN')}")
CSRF_TRUSTED_ORIGINS.extend([
    'https://*.railway.app',
    'http://localhost:5173',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
])

# SECURE PROXY SETTINGS (for Railway)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

print("=" * 50)
print("🚀 Django Settings loaded successfully!")
print(f"📱 DEBUG mode: {DEBUG}")
print(f"🌐 Allowed Hosts: {ALLOWED_HOSTS}")
print(f"🔗 CORS Origins: {CORS_ALLOWED_ORIGINS}")
print(f"🔒 CSRF Trusted Origins: {CSRF_TRUSTED_ORIGINS}")
print("=" * 50)