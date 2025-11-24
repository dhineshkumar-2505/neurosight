"""
Configuration Template for NeuroSight
Copy this file to config.py and fill in your actual credentials
"""

import os

# Flask Configuration
SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
DEBUG = True

# Email Configuration (Gmail SMTP)
# Get Gmail App Password: https://myaccount.google.com/apppasswords
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'your-email@gmail.com'
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'your-gmail-app-password'
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'your-email@gmail.com'

# Google OAuth Configuration
# Get credentials: https://console.cloud.google.com/apis/credentials
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or 'your-google-client-id.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') or 'your-google-client-secret'
GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'

# Database Configuration
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/neurosight.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False
