from pathlib import Path
import os
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# # load env variables in development
project_folder = os.path.expanduser(BASE_DIR)
load_dotenv(os.path.join(project_folder, '.env'))

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ['DEBUG'] == "True"

ALLOWED_HOSTS = os.environ["DJANGO_ALLOWED_HOSTS"].split(',')
try:
    CORS_ORIGIN_WHITELIST = os.environ["CORS_ORIGIN_WHITELIST"].split(',')
except KeyError:
    CORS_ORIGIN_WHITELIST = []

try:
    CORS_ALLOW_CREDENTIALS = os.environ["CORS_ALLOW_CREDENTIALS"] == "True"
except KeyError:
    pass
# it allows to adding cookies to cross site requests
# The value of the 'Access-Control-Allow-Credentials' header in the response is '' which must be 'true'
# when the request's credentials mode is 'include

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app',
    'rest_framework',
    'corsheaders',
    'django_cleanup.apps.CleanupConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # here
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hikegear_backend.urls'

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
                'app.context_processors.frontend_url'
            ],
        },
    },
]

WSGI_APPLICATION = 'hikegear_backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ["DB_NAME"],
        'USER': os.environ["DB_USER"],
        'PASSWORD': os.environ["DB_PASSWORD"],
        'HOST': os.environ["DB_HOST"],
        'PORT': '5432',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Warsaw'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/backend/static/'
STATIC_ROOT = 'static'

AUTH_USER_MODEL = 'app.MyUser'

CSRF_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_HTTPONLY = True

CSRF_COOKIE_SECURE = os.environ["CSRF_COOKIE_SECURE"] == 'True'
SESSION_COOKIE_SECURE = os.environ["SESSION_COOKIE_SECURE"] == 'True'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtpout.secureserver.net'
EMAIL_USE_TLS = False
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = os.environ["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = os.environ["EMAIL_HOST_PASSWORD"]
DEFAULT_FROM_EMAIL = 'hikegear.pl <noreply@hikegear.pl>'

PASSWORD_RESET_TIMEOUT = 900  # 15 minutes

FRONTEND_URL = os.environ['FRONTEND_URL']

try:
    FORCE_SCRIPT_NAME = os.environ["FORCE_SCRIPT_NAME"]
except KeyError:
    FORCE_SCRIPT_NAME = None

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    )
}
