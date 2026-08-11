from .base import *

DEBUG = True

if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['localhost', '127.0.0.1', '0.0.0.0', 'testserver']:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

print("DEBUG local.py: DJANGO_SETTINGS_MODULE =", os.getenv("DJANGO_SETTINGS_MODULE"))
print("DEBUG local.py: final ALLOWED_HOSTS =", ALLOWED_HOSTS)

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

# Patient Registration OTP Requirement
REQUIRE_PATIENT_OTP = True

print("Running with local settings.")
