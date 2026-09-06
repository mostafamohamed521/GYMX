from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-gymx-secret-key-2024')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'apps.accounts',
    'apps.dashboard',
    'apps.members',
    'apps.memberships',
    'apps.attendance',
    'apps.payments',
    'apps.coaches',
    'apps.workouts',
    'apps.nutrition',
    'apps.classes',
    'apps.hr',
    'apps.inventory',
    'apps.pos',
    'apps.branches',
    'apps.crm',
    'apps.reports',
    'apps.notifications',
    'apps.finance',
    'apps.settings',
    'apps.portal',
    'apps.website',
    'apps.aifeatures',
    'apps.system',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.system.middleware.maintenance.MaintenanceModeMiddleware',
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
                'config.context_processors.gymx_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# PostgreSQL (uncomment when ready):
# DB_ENGINE lets the same codebase target Postgres (local/other hosts) or
# MySQL (PythonAnywhere's built-in database, since Postgres isn't offered
# there without a separate external service) purely via .env — no code change.
_db_engine = config('DB_ENGINE', default='postgresql')  # 'postgresql' | 'mysql' | 'sqlite3'

if _db_engine == 'sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / config('DB_NAME', default='db.sqlite3'),
        }
    }
elif _db_engine == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='3306'),
            'OPTIONS': {'charset': 'utf8mb4'},
        }
    }
else:
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

# ── Security Settings ──────────────────────────────────────
# These security headers/cookie flags are only safe to force on once the site is
# served over HTTPS. Locally (DEBUG=True, plain http://localhost) they would break
# the dev server, so they're tied to DEBUG being off — i.e. they turn themselves on
# automatically the moment you deploy with DEBUG=False.
SECURE_BROWSER_XSS_FILTER   = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS             = 'DENY'
SECURE_REFERRER_POLICY      = 'same-origin'
CSRF_COOKIE_HTTPONLY        = True

if not DEBUG:
    # PythonAnywhere (and most hosts) terminate HTTPS at their proxy, then
    # forward the request to Django over plain HTTP internally. Without this,
    # Django thinks every request is insecure, so SECURE_SSL_REDIRECT below
    # would redirect every request right back to itself — an infinite loop
    # that makes the whole site unreachable. Safe here because the proxy
    # sets this header itself and it isn't something an external client can
    # spoof through to the app.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    SECURE_HSTS_SECONDS            = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD            = True
    SECURE_SSL_REDIRECT             = True
    SESSION_COOKIE_SECURE           = True
    CSRF_COOKIE_SECURE              = True

# ── Site URL (used to build absolute links in emails/SMS) ────
SITE_URL = config('SITE_URL', default='http://localhost:8000')

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

# ── Logging ────────────────────────────────────────────────
# Without this, logger.warning()/error() calls (e.g. failed OTP delivery,
# account lockouts) only go to Python's ephemeral "last resort" stderr handler
# and are lost the moment the process restarts. This gives them a durable,
# rotating file — and a dedicated 'security' channel for auth-sensitive events
# so they're easy to monitor/alert on separately from ordinary app noise.
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'app_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'app.log',
            'maxBytes': 5 * 1024 * 1024,   # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'security.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'app_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Auth-sensitive events (failed logins, OTP brute-force, lockouts) —
        # written to both the app log and a dedicated security log so they're
        # easy to isolate for monitoring/alerting without adding a new dependency.
        'apps.accounts': {
            'handlers': ['console', 'app_file', 'security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        '': {  # root logger — everything else
            'handlers': ['console', 'app_file'],
            'level': 'WARNING',
        },
    },
}
