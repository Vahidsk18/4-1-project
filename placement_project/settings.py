# placement_project/settings.py

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-here-please-change-this-for-production-and-use-a-proper-random-string' # IMPORTANT: GENERATE A REAL SECRET KEY FOR PRODUCTION

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True # Set to False in production

ALLOWED_HOSTS = [] # Add your domain names here in production, e.g., ['yourdomain.com', 'www.yourdomain.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',  # <-- UNCOMMENT THIS LINE
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework', # If you plan to build APIs (recommended for frontend integration)
    'core', # Your custom user app
    'placement', # Your placement logic app
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

ROOT_URLCONF = 'placement_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], # Points to your project's 'templates' folder
        'APP_DIRS': True, # Allows Django to find templates within individual app directories
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

WSGI_APPLICATION = 'placement_project.wsgi.application'


# Custom User Model (IMPORTANT for role-based login)
AUTH_USER_MODEL = 'core.User'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Use PostgreSQL/MySQL for production
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata' # Set to your time zone, e.g., 'Asia/Kolkata' for IST

USE_I18N = True

USE_TZ = True


# Login Redirect URLs
LOGIN_URL = 'login' # Name of your login URL
LOGIN_REDIRECT_URL = 'home' # Where to redirect after successful login
LOGOUT_REDIRECT_URL = 'login' # Where to redirect after logout

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # For production deployment

# THIS IS THE MISSING KEY SETTING FOR DEVELOPMENT
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files (user uploads like resumes)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session settings for persistent login
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 1209600



# Email settings (use Gmail for testing)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "vskqis@gmail.com"       # replace with your Gmail
EMAIL_HOST_PASSWORD = "qrxb spqg gomf xkry"      # use Gmail App Password, NOT your normal password
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
