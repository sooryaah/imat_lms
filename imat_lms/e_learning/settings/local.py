from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']  # Allow everything in local machine

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
