"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 4.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import environ
from pathlib import Path
from datetime import timedelta
import os
import django_heroku
import dj_database_url

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(BASE_DIR / '.env')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main.apps.MainConfig',
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap5',
    'phonenumber_field',
    'django_daraja',
    'django_heroku',
    'mpesa',
    'notifications',
]

CRISPY_TEMPLATE_PACK = 'bootstrap5'

CRISPY_ALLOWED_TEMPLATE_PACK = 'bootstrap5'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates' )],
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

WSGI_APPLICATION = 'backend.wsgi.application'

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)
# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        
            'ENGINE': 'django.db.backends.postgresql',

            'NAME': os.getenv('DB_NAME'),

            'USER': os.getenv('DB_USER'),

            'PASSWORD': os.getenv('DB_PASSWORD'),

            'HOST': os.getenv('DB_HOST'),

            'PORT': os.getenv('DB_PORT'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/



# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')



PHONENUMBER_DEFAULT_REGION = 'KE'
PHONENUMBER_DB_FORMAT = 'NATIONAL'

LOGOUT_REDIRECT_URL='/login'
LOGIN_REDIRECT_URL = '/home'



EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER=env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD=env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL='chegegitiche254@gmail.com'
EMAIL_USE_TLS=True
EMAIL_PORT = 587

PASSWORD_RESET_FORM = 'main/templates/registration/password_reset_form.html'

ADMIN_TOOLS_INDEX_DASHBOARD = 'backend.dashboard.CustomIndexDashboard'

MPESA_ENVIRONMENT = 'sandbox'

# Credentials for the daraja app

MPESA_CONSUMER_KEY = 'nhCUnCKLL7Lqulu7pihdkxXeMSGnUMpCCirIJaZe9dOtf8v1'
MPESA_CONSUMER_SECRET = 'sXKDXSzfgwkogCirI0lAezP29JQJGyhYxWSDGmwbu9RYz9tBaaL9SzcxEczPScLs'

#Shortcode to use for transactions. For sandbox  use the Shortcode 1 provided on test credentials page

MPESA_SHORTCODE = '174379'

# Shortcode to use for Lipa na MPESA Online (MPESA Express) transactions
# This is only used on sandbox, do not set this variable in production
# For sandbox use the Lipa na MPESA Online Shorcode provided on test credentials page

MPESA_EXPRESS_SHORTCODE = '174379'

# Type of shortcode
# Possible values:
# - paybill (For Paybill)
# - till_number (For Buy Goods Till Number)

MPESA_SHORTCODE_TYPE = 'paybill'

# Lipa na MPESA Online passkey
# Sandbox passkey is available on test credentials page
# Production passkey is sent via email once you go live

MPESA_PASSKEY = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'

# Username for initiator (to be used in B2C, B2B, AccountBalance and TransactionStatusQuery Transactions)

MPESA_INITIATOR_USERNAME = 'testapi'

# Plaintext password for initiator (to be used in B2C, B2B, AccountBalance and TransactionStatusQuery Transactions)

MPESA_INITIATOR_SECURITY_CREDENTIAL = 'Safaricom999!*!'


MPESA_CONFIG = {
    'CONSUMER_KEY': 'nhCUnCKLL7Lqulu7pihdkxXeMSGnUMpCCirIJaZe9dOtf8v1',
    'CONSUMER_SECRET': 'sXKDXSzfgwkogCirI0lAezP29JQJGyhYxWSDGmwbu9RYz9tBaaL9SzcxEczPScLs',
    'CERTIFICATE_FILE': None,
    'HOST_NAME': 'https://558d-41-90-187-109.ngrok.io',
    'PASS_KEY': 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919',
    'SAFARICOM_API': 'https://sandbox.safaricom.co.ke',
    'AUTH_URL': '/oauth/v1/generate?grant_type=client_credentials',
    'SHORT_CODE': '174379',
    'TILL_NUMBER': None,
    'TRANSACTION_TYPE': 'CustomerBuyGoodsOnline',
}




