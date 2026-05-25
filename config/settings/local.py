from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# In local development, we don't strictly require HTTPS for cookies
SESSION_COOKIE_SECURE = False  
CSRF_COOKIE_SECURE = False

# ==========================================
# LOCAL DEVELOPMENT OVERRIDES
# ==========================================
# Run Celery tasks synchronously locally without requiring Redis or Worker
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

print("Running with local settings.")
