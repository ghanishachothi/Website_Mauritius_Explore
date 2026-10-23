from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-change-this-before-deploying'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Our apps (all share ONE database: db.sqlite3)
    'apps.explore',
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

ROOT_URLCONF = 'mauritius_explore.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # shared base.html + partials
        'APP_DIRS': True,                   # each app's own templates/<app>/ folder
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.explore.context_processors.site_nav',
            ],
        },
    },
]

WSGI_APPLICATION = 'mauritius_explore.wsgi.application'

# ONE database for the whole website
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Indian/Mauritius'
USE_I18N = True
USE_TZ = True

# CSS / JS / design images that are part of the code
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Photos uploaded through the admin (events, destinations, guides...)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'core:home'

LOGOUT_REDIRECT_URL = 'core:home'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

JAZZMIN_SETTINGS = {
    "site_title": "Mauritius Explore Admin",
    "site_header": "Mauritius Explore",
    "welcome_sign": "Welcome to Mauritius Explore admin",
    "site_url": "/",
    "topmenu_links": [
        {"name": "Dashboard", "url": "admin_dashboard:dashboard"},
        {"name": "Website", "url": "core:home"},
    ],
    "usermenu_links": [
        {"name": "Back to website", "url": "core:home"},
    ],
}


# --- shared database switch: SQLite by default, Supabase when a .env file is present ---
import os as _os
from pathlib import Path as _Path
_env = _Path(__file__).resolve().parent.parent / '.env'
if _env.exists():
    for _line in _env.read_text(encoding='utf-8').splitlines():
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _k, _v = _line.split('=', 1)
            _os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))
if _os.environ.get('DATABASE_URL'):
    from urllib.parse import urlparse as _urlparse, unquote as _unquote
    _u = _urlparse(_os.environ['DATABASE_URL'])
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': (_u.path or '/postgres').lstrip('/') or 'postgres',
        'USER': _unquote(_u.username or ''), 'PASSWORD': _unquote(_u.password or ''),
        'HOST': _u.hostname, 'PORT': _u.port or 5432,
        'OPTIONS': {'sslmode': 'require'}, 'DISABLE_SERVER_SIDE_CURSORS': True, 'CONN_MAX_AGE': 60, 'CONN_HEALTH_CHECKS': True }}
if _os.environ.get('SUPABASE_S3_KEY'):
    _static = globals().get('STORAGES', {}).get('staticfiles', {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'})
    STORAGES = {
        'default': {'BACKEND': 'storages.backends.s3.S3Storage', 'OPTIONS': {
            'bucket_name': _os.environ['SUPABASE_BUCKET'], 'endpoint_url': _os.environ['SUPABASE_S3_ENDPOINT'],
            'access_key': _os.environ['SUPABASE_S3_KEY'], 'secret_key': _os.environ['SUPABASE_S3_SECRET'],
            'region_name': _os.environ.get('SUPABASE_S3_REGION', 'us-east-1'),
            'custom_domain': _os.environ['SUPABASE_PUBLIC_BASE'].replace('https://', '').rstrip('/'),
            'addressing_style': 'path', 'signature_version': 's3v4',
            'querystring_auth': False, 'file_overwrite': False, 'default_acl': None}},
        'staticfiles': _static,
    }
