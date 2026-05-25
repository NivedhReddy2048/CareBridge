from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# In local development, we don't strictly require HTTPS for cookies
SESSION_COOKIE_SECURE = False  
CSRF_COOKIE_SECURE = False

print("Running with local settings.")
