# NeuroSight Configuration File
# IMPORTANT: Do not commit this file to version control!

# Flask Secret Key (keep this secret!)
SECRET_KEY = 'your-secret-key-here-change-this-in-production'

# Google OAuth 2.0 Configuration
# Get these from: https://console.cloud.google.com/
GOOGLE_CLIENT_ID = 'your-google-client-id.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = 'your-google-client-secret'

# Email Configuration (Gmail)
# Use Gmail App Password, not your regular password
# Get App Password from: https://myaccount.google.com/apppasswords
MAIL_USERNAME = 'asuproject0112@gmail.com'  # Your Gmail address
MAIL_PASSWORD = 'your-16-character-app-password'  # Gmail App Password

# Application URL (change in production)
APP_URL = 'http://localhost:5000'

# Database
SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/neurosight.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False
