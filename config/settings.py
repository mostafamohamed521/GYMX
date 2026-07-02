from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-gymx-secret-key-2024')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.accounts',
    'apps.dashboard',
    'apps.members',
    'apps.memberships',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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


 # PostgreSQL (uncomment when ready):
DATABASES = {
     'default': {
         'ENGINE': 'django.db.backends.postgresql',
         'NAME': config('DB_NAME'),
         'USER': config('DB_USER'),
         'PASSWORD': config('DB_PASSWORD'),
         'HOST': config('DB_HOST', default='localhost'),
         'PORT': config('DB_PORT', default='5432'),
     }
 }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Cairo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/auth/login/'

SESSION_COOKIE_AGE = 86400
SESSION_SAVE_EVERY_REQUEST = True

# ── Production Security Settings (uncomment when deploying) ──
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# X_FRAME_OPTIONS = 'DENY'

# ── Email Configuration ───────────────────────────────────
EMAIL_BACKEND     = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST        = config('EMAIL_HOST',    default='smtp.gmail.com')
EMAIL_PORT        = config('EMAIL_PORT',    default=587, cast=int)
EMAIL_USE_TLS     = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER   = config('EMAIL_HOST_USER',   default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = config('DEFAULT_FROM_EMAIL', default='GymX <noreply@gymx.com>')

# ── Twilio Configuration ──────────────────────────────────
TWILIO_ACCOUNT_SID  = config('TWILIO_ACCOUNT_SID',  default='')
TWILIO_AUTH_TOKEN   = config('TWILIO_AUTH_TOKEN',   default='')
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER', default='')
