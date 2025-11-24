import os
import secrets
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from authlib.integrations.flask_client import OAuth
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import requests
from transformers import ViTFeatureExtractor, ViTForImageClassification, SwinForImageClassification, ConvNextForImageClassification
from PIL import Image
import torch
import torch.nn.functional as F
import numpy as np
import tensorflow as tf
from tensorflow import keras
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from models import db, User, AnalysisHistory, init_db
from auth_utils import validate_email, validate_password

app = Flask(__name__, static_folder="static", template_folder="templates")

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Security Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'neurosight-secret-key-change-in-production-2024')

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///neurosight.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email Configuration (Gmail SMTP)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Google OAuth Configuration
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')
app.config['GOOGLE_DISCOVERY_URL'] = os.environ.get('GOOGLE_DISCOVERY_URL', 'https://accounts.google.com/.well-known/openid-configuration')


# Initialize extensions
init_db(app)
mail = Mail(app)
oauth = OAuth(app)

# Register Google OAuth client
oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Token serializer for password reset
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Email sending function for welcome message
def send_welcome_email(user):
    """Send welcome email after successful onboarding"""
    try:
        msg = Message(
            subject='Welcome to NeuroSight - Registration Successful!',
            recipients=[user.email]
        )
        
        # Create HTML email body
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #0EA5E9 0%, #06B6D4 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .content {{
                    background: #ffffff;
                    padding: 30px;
                    border: 1px solid #e2e8f0;
                }}
                .details-box {{
                    background: #f8fafc;
                    border-left: 4px solid #0EA5E9;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 5px;
                }}
                .details-box h3 {{
                    color: #0EA5E9;
                    margin-top: 0;
                }}
                .detail-row {{
                    padding: 8px 0;
                    border-bottom: 1px solid #e2e8f0;
                }}
                .detail-row:last-child {{
                    border-bottom: none;
                }}
                .detail-label {{
                    font-weight: bold;
                    color: #64748b;
                    display: inline-block;
                    width: 180px;
                }}
                .detail-value {{
                    color: #0f172a;
                }}
                .footer {{
                    background: #f8fafc;
                    padding: 20px;
                    text-align: center;
                    border-radius: 0 0 10px 10px;
                    color: #64748b;
                    font-size: 14px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #0EA5E9 0%, #06B6D4 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .icon {{
                    font-size: 48px;
                    margin-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="icon">🧠</div>
                <h1>Welcome to NeuroSight!</h1>
                <p>Your registration is complete</p>
            </div>
            
            <div class="content">
                <h2>Dear Dr. {user.full_name},</h2>
                
                <p>Congratulations! Your NeuroSight account has been successfully created and verified.</p>
                
                <p>We're excited to have you join our community of healthcare professionals using AI-powered brain disease detection technology.</p>
                
                <div class="details-box">
                    <h3>📋 Your Registration Details</h3>
                    <div class="detail-row">
                        <span class="detail-label">Full Name:</span>
                        <span class="detail-value">{user.full_name}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Email:</span>
                        <span class="detail-value">{user.email}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Medical Reg. No:</span>
                        <span class="detail-value">{user.medical_registration_no or 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Role:</span>
                        <span class="detail-value">{user.specialization or 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Years of Experience:</span>
                        <span class="detail-value">{user.years_of_experience or 'N/A'} years</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Hospital/Clinic:</span>
                        <span class="detail-value">{user.hospital or 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Department:</span>
                        <span class="detail-value">{user.department or 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Registration Date:</span>
                        <span class="detail-value">{user.created_at.strftime('%B %d, %Y at %I:%M %p')}</span>
                    </div>
                </div>
                
                <h3>🚀 What's Next?</h3>
                <ul>
                    <li><strong>Upload Brain Scans:</strong> Start analyzing MRI scans for various brain diseases</li>
                    <li><strong>View Analysis History:</strong> Track all your previous analyses</li>
                    <li><strong>Generate Reports:</strong> Download professional PDF reports for your patients</li>
                    <li><strong>Manage Profile:</strong> Update your professional details anytime</li>
                </ul>
                
                <center>
                    <a href="http://localhost:5000/dashboard" class="button">Go to Dashboard</a>
                </center>
                
                <h3>💡 Quick Tips</h3>
                <ul>
                    <li>Ensure MRI scans are in supported formats (JPG, PNG, JPEG)</li>
                    <li>For best results, use high-quality brain scan images</li>
                    <li>Review the confidence scores provided with each analysis</li>
                    <li>Keep your professional credentials up to date</li>
                </ul>
                
                <p><strong>Need Help?</strong> If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                
                <p>Thank you for choosing NeuroSight. We're committed to supporting you in providing the best possible care for your patients.</p>
                
                <p>Best regards,<br>
                <strong>The NeuroSight Team</strong></p>
            </div>
            
            <div class="footer">
                <p>This is an automated message from NeuroSight Brain Disease Detection System</p>
                <p>© 2024 NeuroSight. All rights reserved.</p>
                <p style="font-size: 12px; margin-top: 10px;">
                    If you did not register for this account, please contact us immediately.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version as fallback
        msg.body = f"""
        Welcome to NeuroSight!
        
        Dear Dr. {user.full_name},
        
        Congratulations! Your NeuroSight account has been successfully created and verified.
        
        Your Registration Details:
        - Full Name: {user.full_name}
        - Email: {user.email}
        - Medical Registration No: {user.medical_registration_no or 'N/A'}
        - Role: {user.specialization or 'N/A'}
        - Years of Experience: {user.years_of_experience or 'N/A'} years
        - Hospital/Clinic: {user.hospital or 'N/A'}
        - Department: {user.department or 'N/A'}
        - Registration Date: {user.created_at.strftime('%B %d, %Y at %I:%M %p')}
        
        What's Next?
        - Upload Brain Scans for analysis
        - View your analysis history
        - Generate professional PDF reports
        - Manage your profile
        
        Visit your dashboard: http://localhost:5000/dashboard
        
        Thank you for choosing NeuroSight!
        
        Best regards,
        The NeuroSight Team
        """
        
        mail.send(msg)
        print(f"✓ Welcome email sent to {user.email}")
        return True
    except Exception as e:
        print(f"✗ Failed to send welcome email to {user.email}: {str(e)}")
        return False


def send_otp_email(user, otp_code):
    """Send OTP email for email verification"""
    try:
        msg = Message(
            subject='NeuroSight - Email Verification Code',
            recipients=[user.email]
        )
        
        # Create HTML email body
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #0EA5E9 0%, #06B6D4 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .content {{
                    background: #ffffff;
                    padding: 40px;
                    border: 1px solid #e2e8f0;
                }}
                .otp-box {{
                    background: #f8fafc;
                    border: 3px dashed #0EA5E9;
                    padding: 30px;
                    margin: 30px 0;
                    text-align: center;
                    border-radius: 10px;
                }}
                .otp-code {{
                    font-size: 48px;
                    font-weight: bold;
                    color: #0EA5E9;
                    letter-spacing: 10px;
                    font-family: 'Courier New', monospace;
                }}
                .warning-box {{
                    background: #FEF3C7;
                    border-left: 4px solid #F59E0B;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 5px;
                }}
                .footer {{
                    background: #f8fafc;
                    padding: 20px;
                    text-align: center;
                    border-radius: 0 0 10px 10px;
                    color: #64748b;
                    font-size: 14px;
                }}
                .icon {{
                    font-size: 48px;
                    margin-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="icon">🔐</div>
                <h1>Email Verification</h1>
                <p>Verify your NeuroSight account</p>
            </div>
            
            <div class="content">
                <h2>Hello {user.full_name},</h2>
                
                <p>Thank you for registering with NeuroSight! To complete your registration, please verify your email address using the code below:</p>
                
                <div class="otp-box">
                    <p style="margin: 0; color: #64748b; font-size: 14px; margin-bottom: 10px;">YOUR VERIFICATION CODE</p>
                    <div class="otp-code">{otp_code}</div>
                    <p style="margin: 10px 0 0 0; color: #64748b; font-size: 14px;">Valid for 10 minutes</p>
                </div>
                
                <p><strong>How to verify:</strong></p>
                <ol>
                    <li>Return to the registration page</li>
                    <li>Enter the 6-digit code above</li>
                    <li>Click "Verify Email"</li>
                </ol>
                
                <div class="warning-box">
                    <strong>⚠️ Security Notice:</strong>
                    <ul style="margin: 10px 0 0 0;">
                        <li>Never share this code with anyone</li>
                        <li>NeuroSight will never ask for this code via phone or email</li>
                        <li>This code expires in 10 minutes</li>
                        <li>You have 5 attempts to enter the correct code</li>
                    </ul>
                </div>
                
                <p>If you didn't request this code, please ignore this email or contact our support team if you have concerns.</p>
                
                <p>Best regards,<br>
                <strong>The NeuroSight Team</strong></p>
            </div>
            
            <div class="footer">
                <p>This is an automated message from NeuroSight Brain Disease Detection System</p>
                <p>© 2024 NeuroSight. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version as fallback
        msg.body = f"""
        NeuroSight - Email Verification
        
        Hello {user.full_name},
        
        Thank you for registering with NeuroSight!
        
        Your verification code is: {otp_code}
        
        This code is valid for 10 minutes.
        
        How to verify:
        1. Return to the registration page
        2. Enter the 6-digit code
        3. Click "Verify Email"
        
        Security Notice:
        - Never share this code with anyone
        - This code expires in 10 minutes
        - You have 5 attempts to enter the correct code
        
        If you didn't request this code, please ignore this email.
        
        Best regards,
        The NeuroSight Team
        """
        
        mail.send(msg)
        print(f"✓ OTP email sent to {user.email}")
        return True
    except Exception as e:
        print(f"✗ Failed to send OTP email to {user.email}: {str(e)}")
        return False



# Configuration
UPLOAD_FOLDER = os.path.join(app.static_folder, "uploads")
REPORTS_FOLDER = os.path.join(app.static_folder, "reports")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

# Load feature extractor
print("Loading ViT feature extractor...")
feature_extractor = ViTFeatureExtractor.from_pretrained('google/vit-base-patch16-224-in21k')

# Disease configurations
DISEASE_CONFIG = {
    'ms': {
        'name': 'Multiple Sclerosis',
        'model_path': 'multiple_sclerosis.pth',
        'class_mapping': {0: 'Control-Axial', 1: 'Control-Sagittal', 2: 'MS-Axial', 3: 'MS-Sagittal'}
    },
    'alzheimer': {
        'name': "Alzheimer's Disease",
        'model_path': 'alzhimermodel.pth',
        'class_mapping': {0: 'Mild-alzhimer', 1: 'Moderate-alzhimer', 2: 'Non-alzhimer', 3: 'VeryMild-alzhimer'}
    },
   
    'dementia': {
        'name': 'Dementia',
        'model_path': 'dementia_detection_model_2.h5',
        'class_mapping': {0: 'Non-Demented', 1: 'Very-Mild-Demented', 2: 'Mild-Demented', 3: 'Moderate-Demented'}
    },
    'stroke': {
        'name': 'Stroke',
        'model_path': 'stroke.pth',
        'class_mapping': {0: 'Normal 😊', 1: 'Stroke 💔'}
    }
}

def map_convnext_keys(state_dict):
    new_dict = {}
    for k, v in state_dict.items():
        new_k = k
        # Map stem
        if k.startswith('stem.0'):
            new_k = k.replace('stem.0', 'convnext.embeddings.patch_embeddings')
        elif k.startswith('stem.1'):
            new_k = k.replace('stem.1', 'convnext.embeddings.layernorm')
            
        # Map stages
        elif k.startswith('stages'):
            # stages.0.blocks.0 -> convnext.encoder.stages.0.layers.0
            parts = k.split('.')
            stage_idx = parts[1]
            block_idx = parts[3]
            rest = '.'.join(parts[4:])
            
            prefix = f'convnext.encoder.stages.{stage_idx}.layers.{block_idx}'
            
            if 'gamma' in rest:
                new_k = f'{prefix}.layer_scale_parameter'
            elif 'conv_dw' in rest:
                new_k = f'{prefix}.dwconv.{rest.replace("conv_dw.", "")}'
            elif 'norm' in rest:
                new_k = f'{prefix}.layernorm.{rest.replace("norm.", "")}'
            elif 'mlp.fc1' in rest:
                new_k = f'{prefix}.pwconv1.{rest.replace("mlp.fc1.", "")}'
            elif 'mlp.fc2' in rest:
                new_k = f'{prefix}.pwconv2.{rest.replace("mlp.fc2.", "")}'
            elif 'downsample' in k:
                 # stages.0.downsample.0 -> convnext.encoder.stages.0.downsampling_layer.0
                 ds_idx = parts[3]
                 rest_ds = '.'.join(parts[4:])
                 new_k = f'convnext.encoder.stages.{stage_idx}.downsampling_layer.{ds_idx}.{rest_ds}'
        
        # Map head
        elif k.startswith('head'):
            if 'fc' in k:
                new_k = k.replace('head.fc', 'classifier')
            elif 'norm' in k:
                new_k = k.replace('head.norm', 'convnext.layernorm')
                
        new_dict[new_k] = v
    return new_dict

def load_model(model_path, num_labels=4):
    """Load PyTorch (ViT/ConvNeXt) or TensorFlow/Keras (EfficientNet) model"""
    try:
        full_path = os.path.join(os.getcwd(), model_path)
        
        # Check if this is a Keras/TensorFlow model (.h5)
        if model_path.lower().endswith('.h5'):
            print(f"  Loading Keras model for {model_path}...")
            model = keras.models.load_model(full_path)
            model.model_type = 'keras'  # Tag for later use
            print(f"✓ Loaded Keras model: {model_path}")
            return model
        
        # PyTorch models
        if 'stroke' in model_path:
            # Stroke model is a ConvNeXt (Base) with 1 output (binary)
            print(f"  Loading ConvNeXt for {model_path}...")
            try:
                model = ConvNextForImageClassification.from_pretrained(
                    'facebook/convnext-base-224-22k-1k', 
                    num_labels=num_labels, 
                    ignore_mismatched_sizes=True
                )
                # Load and map weights
                state_dict = torch.load(full_path, map_location=torch.device('cpu'))
                new_state_dict = map_convnext_keys(state_dict)
                model.load_state_dict(new_state_dict)
                model.model_type = 'pytorch'
                
            except Exception as e:
                print(f"  Warning: Could not load ConvNeXt config: {e}")
                return None
        else:
            # ViT models
            model = ViTForImageClassification.from_pretrained('google/vit-base-patch16-224-in21k', num_labels=num_labels)
            state_dict = torch.load(full_path, map_location=torch.device('cpu'))
            model.load_state_dict(state_dict)
            model.model_type = 'pytorch'
            
        model.eval()
        print(f"✓ Loaded model: {model_path}")
        return model
    except Exception as e:
        print(f"✗ Could not load model {model_path}: {str(e)}")
        return None

# Load all available models
print("\nLoading disease detection models...")
models = {}
for disease_key, config in DISEASE_CONFIG.items():
    # Stroke model has 1 output node (binary), others have 4
    num_labels = 1 if disease_key == 'stroke' else 4
    model = load_model(config['model_path'], num_labels=num_labels)
    if model:
        models[disease_key] = model

print(f"\nLoaded {len(models)} out of {len(DISEASE_CONFIG)} models successfully.\n")


# ============ HELPER FUNCTIONS ============

def get_google_provider_cfg():
    """Fetch Google's OAuth 2.0 provider configuration"""
    try:
        return requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()
    except:
        return None

def send_reset_email(user):
    """Send password reset email to user"""
    try:
        # Generate reset token (expires in 1 hour)
        token = serializer.dumps(user.email, salt='password-reset-salt')
        
        # Create reset URL
        reset_url = url_for('reset_password', token=token, _external=True)
        
        # Create email message
        msg = Message(
            subject='NeuroSight - Password Reset Request',
            recipients=[user.email],
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Email body
        msg.html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="color: white; margin: 0;">🧠 NeuroSight</h1>
                        <p style="color: #f0f0f0; margin: 10px 0 0 0;">AI-Powered Brain Disease Detection</p>
                    </div>
                    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                        <h2 style="color: #667eea;">Password Reset Request</h2>
                        <p>Hello <strong>{user.full_name}</strong>,</p>
                        <p>We received a request to reset your password for your NeuroSight account.</p>
                        <p>Click the button below to reset your password:</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{reset_url}" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Reset Password</a>
                        </div>
                        <p style="color: #666; font-size: 14px;">Or copy and paste this link into your browser:</p>
                        <p style="background: white; padding: 10px; border-radius: 5px; word-break: break-all; font-size: 12px;">{reset_url}</p>
                        <p style="color: #666; font-size: 14px; margin-top: 30px;">
                            <strong>This link will expire in 1 hour.</strong><br>
                            If you didn't request this password reset, please ignore this email.
                        </p>
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                        <p style="color: #999; font-size: 12px; text-align: center;">
                            NeuroSight - Rajalakshmi Engineering College<br>
                            Contact: asuproject0112@gmail.com
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def verify_reset_token(token, expiration=3600):
    """Verify password reset token (default 1 hour expiration)"""
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        return email
    except (SignatureExpired, BadSignature):
        return None


# ============ AUTHENTICATION ROUTES ============

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        role = request.form.get('role', '').strip()
        hospital = request.form.get('hospital', '').strip()
        license_number = request.form.get('license_number', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # Validation
        if not all([email, password, full_name, role]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('register.html')
        
        if not validate_email(email):
            flash('Invalid email address.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, 'danger')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'warning')
            return redirect(url_for('login'))
        
        # Create new user
        new_user = User(
            email=email,
            full_name=full_name,
            role=role,
            hospital=hospital,
            license_number=license_number,
            phone=phone,
            is_verified=True  # Auto-verify for now
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


# ============================================================================
# OTP-BASED REGISTRATION API ENDPOINTS
# ============================================================================

@app.route('/api/register', methods=['POST'])
def api_register():
    """API endpoint for email/password registration with OTP verification"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        
        # Validation
        if not all([email, password, full_name]):
            return {'success': False, 'error': 'Please fill in all required fields'}, 400
        
        if not validate_email(email):
            return {'success': False, 'error': 'Invalid email address'}, 400
        
        is_valid, message = validate_password(password)
        if not is_valid:
            return {'success': False, 'error': message}, 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            if existing_user.email_verified:
                return {'success': False, 'error': 'Email already registered. Please login.'}, 400
            else:
                # User exists but not verified - resend OTP
                otp_code = existing_user.generate_otp()
                db.session.commit()
                send_otp_email(existing_user, otp_code)
                return {
                    'success': True,
                    'message': 'Verification email resent',
                    'user_id': existing_user.id,
                    'email': email
                }, 200
        
        # Create new user (not verified yet)
        new_user = User(
            email=email,
            full_name=full_name,
            role='doctor',  # Default role, will be set during onboarding
            email_verified=False,
            is_active=True
        )
        new_user.set_password(password)
        
        # Generate OTP
        otp_code = new_user.generate_otp()
        
        db.session.add(new_user)
        db.session.commit()
        
        # Send OTP email
        send_otp_email(new_user, otp_code)
        
        print(f"✓ New user registered: {email}, OTP: {otp_code}")
        
        return {
            'success': True,
            'message': 'Registration successful! Please check your email for verification code.',
            'user_id': new_user.id,
            'email': email
        }, 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': f'Registration failed: {str(e)}'}, 500


@app.route('/api/verify-otp', methods=['POST'])
def api_verify_otp():
    """API endpoint to verify OTP code"""
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        otp_code = data.get('otp_code', '').strip()
        
        if not user_id or not otp_code:
            return {'success': False, 'error': 'User ID and OTP code are required'}, 400
        
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}, 404
        
        # Verify OTP
        success, message = user.verify_otp(otp_code)
        
        if success:
            db.session.commit()
            
            # Don't auto-login, redirect to login page
            print(f"✓ Email verified for: {user.email}")
            
            return {
                'success': True,
                'message': 'Email verified successfully! Please login with your credentials.',
                'redirect': url_for('login')
            }, 200
        else:
            db.session.commit()  # Save attempt count
            return {'success': False, 'error': message}, 400
            
    except Exception as e:
        db.session.rollback()
        print(f"OTP verification error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': f'Verification failed: {str(e)}'}, 500


@app.route('/api/resend-otp', methods=['POST'])
def api_resend_otp():
    """API endpoint to resend OTP code"""
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        
        if not user_id:
            return {'success': False, 'error': 'User ID is required'}, 400
        
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}, 404
        
        if user.email_verified:
            return {'success': False, 'error': 'Email already verified'}, 400
        
        # Generate new OTP
        otp_code = user.generate_otp()
        db.session.commit()
        
        # Send email
        send_otp_email(user, otp_code)
        
        print(f"✓ OTP resent to: {user.email}, New OTP: {otp_code}")
        
        return {
            'success': True,
            'message': 'Verification code resent successfully!'
        }, 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Resend OTP error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': f'Failed to resend code: {str(e)}'}, 500




@app.route('/verify-email')
def verify_email():
    """Email verification page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('verify_email.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('login.html')
            
            # Check email verification (grandfather existing users)
            # If email_verified is None, it's an old user - allow login
            # If email_verified is False, require verification
            if user.email_verified is False:
                flash('Please verify your email address before logging in. Check your inbox for the verification code.', 'warning')
                return render_template('login.html', show_resend_verification=True, user_email=user.email, user_id=user.id)
            
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('landing'))


# ============ GOOGLE OAUTH ROUTES ============

@app.route('/auth/google')
def google_login():
    """Initiate Google OAuth login"""
    # Check if OAuth is configured
    if not app.config['GOOGLE_CLIENT_ID'] or not app.config['GOOGLE_CLIENT_SECRET']:
        flash('Google OAuth is not configured. Please contact administrator.', 'warning')
        return redirect(url_for('login'))
    
    redirect_uri = url_for('google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route('/auth/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    try:
        # Get the token from Google
        token = oauth.google.authorize_access_token()
        
        # Get user info from Google
        user_info = token.get('userinfo')
        if not user_info:
            user_info = oauth.google.parse_id_token(token)
        
        # Extract user details
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0])
        google_id = user_info.get('sub')
        picture = user_info.get('picture')  # Get profile photo
        
        if not email:
            flash("Unable to get email from Google.", "danger")
            return redirect(url_for('login'))
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Create new user with Google OAuth
            user = User(
                email=email,
                full_name=name,
                google_id=google_id,
                profile_photo_url=picture,
                role='doctor',  # Default role
                is_verified=True,
                is_active=True,
                email_verified=True,  # Google users are verified by definition
                onboarding_completed=False  # Require onboarding
            )
            db.session.add(user)
            db.session.commit()
            flash(f'Welcome to NeuroSight, {name}! Please complete your profile.', 'info')
        else:
            # Update google_id and profile photo if not set
            if not user.google_id:
                user.google_id = google_id
            if not user.profile_photo_url and picture:
                user.profile_photo_url = picture
            
            # Ensure email is verified for Google login
            if not user.email_verified:
                user.email_verified = True
                
            db.session.commit()
        
        # Log the user in
        login_user(user)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Check if user needs onboarding
        if user.needs_onboarding():
            return redirect(url_for('onboarding'))
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        print(f"OAuth error: {e}")
        flash('Authentication failed. Please try again.', 'danger')
        return redirect(url_for('login'))



# ============ PASSWORD RESET ROUTES ============

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Please enter your email address.', 'warning')
            return render_template('forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Send reset email
            if send_reset_email(user):
                flash('Password reset instructions have been sent to your email.', 'success')
            else:
                flash('Unable to send email. Please contact support.', 'danger')
        else:
            # Don't reveal if email exists or not (security best practice)
            flash('If that email exists in our system, you will receive password reset instructions.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Verify token
    email = verify_reset_token(token)
    if not email:
        flash('Invalid or expired reset link. Please request a new one.', 'danger')
        return redirect(url_for('forgot_password'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not password or not confirm_password:
            flash('Please fill in all fields.', 'warning')
            return render_template('reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)
        
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, 'danger')
            return render_template('reset_password.html', token=token)
        
        # Update password
        user.set_password(password)
        db.session.commit()
        
        flash('Your password has been reset successfully. Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)


# ============ ONBOARDING ROUTES ============

@app.route('/onboarding')
@login_required
def onboarding():
    """Onboarding page for collecting doctor and hospital details"""
    # If user already completed onboarding, redirect to dashboard
    if not current_user.needs_onboarding():
        return redirect(url_for('dashboard'))
    
    return render_template('onboarding.html')


@app.route('/api/prefill-google-profile', methods=['GET'])
@login_required
def prefill_google_profile():
    """API endpoint to get Google profile data for prefilling"""
    try:
        user_data = {
            'full_name': current_user.full_name or '',
            'email': current_user.email or '',
            'phone': current_user.phone or '',
            'profile_photo_url': current_user.profile_photo_url or '',
            'medical_registration_no': current_user.medical_registration_no or '',
            'specialization': current_user.specialization or '',
            'years_of_experience': current_user.years_of_experience or '',
            'clinic_timing': current_user.clinic_timing or '',
            'hospital': current_user.hospital or '',
            'hospital_id': current_user.hospital_id or '',
            'hospital_address': current_user.hospital_address or '',
            'department': current_user.department or '',
            'hospital_phone': current_user.hospital_phone or ''
        }
        
        return {'success': True, 'data': user_data}, 200
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500


@app.route('/api/complete-onboarding', methods=['POST'])
@login_required
def complete_onboarding():
    """API endpoint to save onboarding data"""
    try:
        data = request.get_json()
        print(f"=== Onboarding Data Received ===")
        print(f"Data: {data}")
        
        if not data:
            return {'success': False, 'error': 'No data provided'}, 400
        
        # Validate required doctor details
        required_doctor_fields = ['full_name', 'medical_registration_no', 'specialization', 
                                 'phone', 'email', 'years_of_experience']
        for field in required_doctor_fields:
            if not data.get(field):
                return {'success': False, 'error': f'{field} is required'}, 400
        
        # Validate required hospital details
        required_hospital_fields = ['hospital', 'hospital_id', 'department']
        for field in required_hospital_fields:
            if not data.get(field):
                return {'success': False, 'error': f'{field} is required'}, 400
        
        # Validate confirmation checkbox
        if not data.get('confirmed'):
            return {'success': False, 'error': 'Please confirm that your details are accurate'}, 400
        
        # Update user with doctor details
        current_user.full_name = data.get('full_name')
        current_user.medical_registration_no = data.get('medical_registration_no')
        current_user.specialization = data.get('specialization')
        current_user.phone = data.get('phone')
        current_user.email = data.get('email')
        current_user.years_of_experience = int(data.get('years_of_experience', 0))
        current_user.clinic_timing = data.get('clinic_timing', '')
        
        # Update user with hospital details
        current_user.hospital = data.get('hospital')
        current_user.hospital_id = data.get('hospital_id')
        current_user.department = data.get('department')
        current_user.hospital_phone = data.get('hospital_phone', '')
        
        # Optional: Update profile photo if provided
        if data.get('profile_photo_url'):
            current_user.profile_photo_url = data.get('profile_photo_url')
        
        # Optional: Update hospital logo if provided
        if data.get('hospital_logo_url'):
            current_user.hospital_logo_url = data.get('hospital_logo_url')
        
        # Mark onboarding as completed
        current_user.onboarding_completed = True
        
        db.session.commit()
        
        # Send welcome email
        send_welcome_email(current_user)
        
        return {'success': True, 'message': 'Onboarding completed successfully!'}, 200
        
    except ValueError as e:
        db.session.rollback()
        print(f"ValueError in onboarding: {str(e)}")
        print(f"Data received: {data}")
        return {'success': False, 'error': f'Invalid data format: {str(e)}'}, 400
    except Exception as e:
        db.session.rollback()
        print(f"Onboarding error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print(f"Data received: {data}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': f'Failed to save onboarding data: {str(e)}'}, 500


@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    total_analyses = AnalysisHistory.query.filter_by(user_id=current_user.id).count()
    
    # Get analyses from this month
    from datetime import datetime, timedelta
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    recent_analyses = AnalysisHistory.query.filter(
        AnalysisHistory.user_id == current_user.id,
        AnalysisHistory.created_at >= month_start
    ).count()
    
    # Get recent history (last 5)
    recent_history = AnalysisHistory.query.filter_by(user_id=current_user.id)\
        .order_by(AnalysisHistory.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         total_analyses=total_analyses,
                         recent_analyses=recent_analyses,
                         recent_history=recent_history)


@app.route('/history')
@login_required
def history():
    """View analysis history"""
    analyses = AnalysisHistory.query.filter_by(user_id=current_user.id)\
        .order_by(AnalysisHistory.created_at.desc()).all()
    return render_template('history.html', analyses=analyses)


# ============ MAIN APPLICATION ROUTES ============

@app.route('/')
def landing():
    """Landing page"""
    return render_template('landing.html')


@app.route('/detect', methods=['GET', 'POST'])
@login_required  # Require login for detection
def detect():
    """Disease detection page"""
    if request.method == 'POST':
        if 'file' not in request.files or request.files['file'].filename == '':
            flash('Please select an image file.', 'warning')
            return redirect(request.url)
        
        disease_type = request.form.get('disease')
        if not disease_type or disease_type not in DISEASE_CONFIG:
            flash('Please select a valid disease type.', 'warning')
            return redirect(request.url)
        
        if disease_type not in models:
            error_msg = f"{DISEASE_CONFIG[disease_type]['name']} model is not yet configured."
            return render_template('detect.html', error=error_msg, selected_disease=disease_type)
        
        # Get patient information
        patient_info = {
            'name': request.form.get('patient_name', 'N/A'),
            'id': request.form.get('patient_id', 'N/A'),
            'age': request.form.get('patient_age', 'N/A'),
            'scan_date': request.form.get('scan_date', 'N/A')
        }
        
        # Save uploaded file
        file = request.files['file']
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Preprocess and run inference
        image = Image.open(filepath).convert('RGB')
        model = models[disease_type]
        class_mapping = DISEASE_CONFIG[disease_type]['class_mapping']
        
        # Check if this is a Keras or PyTorch model
        if hasattr(model, 'model_type') and model.model_type == 'keras':
            # Keras/TensorFlow model (EfficientNetB3 for dementia)
            # Resize to expected input size (128x128 for this specific model)
            img_array = np.array(image.resize((128, 128)))
            img_array = img_array / 255.0  # Normalize to [0, 1]
            img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
            
            # Predict
            predictions = model.predict(img_array, verbose=0)
            predicted_class_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class_idx]) * 100
            predicted_class = class_mapping[predicted_class_idx]
            confidence = round(confidence, 2)
        else:
            # PyTorch model (ViT or ConvNeXt)
            inputs = feature_extractor(images=image, return_tensors="pt")
            pixel_values = inputs['pixel_values']
            
            with torch.no_grad():
                outputs = model(pixel_values=pixel_values)
                logits = outputs.logits
                
                if disease_type == 'stroke':
                    # Binary classification with 1 output node (ConvNeXt)
                    # Apply sigmoid to get probability of positive class (Stroke)
                    prob = torch.sigmoid(logits).item()
                    
                    # Threshold at 0.5
                    if prob >= 0.5:
                        predicted_class_idx = 1 # Stroke
                        confidence = prob * 100
                    else:
                        predicted_class_idx = 0 # Normal
                        confidence = (1 - prob) * 100
                        
                    predicted_class = class_mapping[predicted_class_idx]
                    confidence = round(confidence, 2)
                else:
                    # Multi-class classification (ViT)
                    predicted_class_idx = logits.argmax(-1).item()
                    predicted_class = class_mapping[predicted_class_idx]
                    probabilities = F.softmax(logits, dim=-1)
                    confidence = probabilities[0][predicted_class_idx].item() * 100
                    confidence = round(confidence, 2)
        
        # Save to database
        analysis = AnalysisHistory(
            user_id=current_user.id,
            patient_name=patient_info['name'],
            patient_id=patient_info['id'],
            patient_age=int(patient_info['age']) if patient_info['age'].isdigit() else None,
            disease_type=disease_type,
            prediction=predicted_class,
            confidence=confidence / 100,
            image_path=filename
        )
        db.session.add(analysis)
        db.session.commit()
        
        image_url = url_for('static', filename=f'uploads/{filename}')
        
        return render_template('detect.html',
                             prediction=predicted_class,
                             confidence=confidence,
                             uploaded_image=image_url,
                             disease_type=disease_type,
                             disease_name=DISEASE_CONFIG[disease_type]['name'],
                             patient_info=patient_info,
                             selected_disease=disease_type)
    
    selected_disease = request.args.get('disease', '')
    return render_template('detect.html', selected_disease=selected_disease)


@app.route('/generate-report', methods=['POST'])
@login_required
def generate_report():
    """Generate PDF report"""
    try:
        patient_name = request.form.get('patient_name', 'N/A')
        patient_id = request.form.get('patient_id', 'N/A')
        patient_age = request.form.get('patient_age', 'N/A')
        scan_date = request.form.get('scan_date', 'N/A')
        disease = request.form.get('disease', 'N/A')
        prediction = request.form.get('prediction', 'N/A')
        confidence = request.form.get('confidence', 'N/A')
        image_path = request.form.get('image_path', '')
        
        disease_name = DISEASE_CONFIG.get(disease, {}).get('name', 'Unknown')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f"NeuroSight_Report_{patient_id}_{timestamp}.pdf"
        pdf_path = os.path.join(REPORTS_FOLDER, pdf_filename)
        
        doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                                rightMargin=50, leftMargin=50,
                                topMargin=50, bottomMargin=50)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom Styles - Premium Design
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#1E40AF'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        section_heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1E3A8A'),
            spaceBefore=15,
            spaceAfter=10,
            fontName='Helvetica-Bold',
            borderWidth=0,
            borderColor=colors.HexColor('#3B82F6'),
            borderPadding=5,
            leftIndent=0
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#334155'),
            leading=16,
            fontName='Helvetica'
        )
        
        # Header with Logo and Title
        story.append(Paragraph("🧠 NeuroSight", title_style))
        story.append(Paragraph("AI-Powered Brain Disease Detection Report", subtitle_style))
        
        # Decorative line
        story.append(Spacer(1, 0.1*inch))
        line_table = Table([['']], colWidths=[6.5*inch])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#3B82F6')),
        ]))
        story.append(line_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Report metadata
        report_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        meta_data = [[Paragraph(f"<b>Report Generated:</b> {report_date}", body_style)]]
        meta_table = Table(meta_data, colWidths=[6.5*inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 0.4*inch))
        
        # Patient Information Section
        story.append(Paragraph("📋 Patient Information", section_heading_style))
        story.append(Spacer(1, 0.15*inch))
        
        patient_data = [
            [Paragraph('<b>Patient Name:</b>', body_style), Paragraph(patient_name, body_style)],
            [Paragraph('<b>Patient ID:</b>', body_style), Paragraph(patient_id, body_style)],
            [Paragraph('<b>Age:</b>', body_style), Paragraph(str(patient_age), body_style)],
            [Paragraph('<b>Scan Date:</b>', body_style), Paragraph(scan_date, body_style)]
        ]
        patient_table = Table(patient_data, colWidths=[2*inch, 4.5*inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#EFF6FF')),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DBEAFE')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        story.append(patient_table)
        story.append(Spacer(1, 0.4*inch))
        
        # Diagnostic Results Section
        story.append(Paragraph("🔬 Diagnostic Results", section_heading_style))
        story.append(Spacer(1, 0.15*inch))
        
        # Determine result color based on prediction
        result_color = colors.HexColor('#FEF3C7') if 'Normal' in str(prediction) or 'Control' in str(prediction) else colors.HexColor('#FEE2E2')
        
        results_data = [
            [Paragraph('<b>Disease Type:</b>', body_style), Paragraph(disease_name, body_style)],
            [Paragraph('<b>Prediction:</b>', body_style), Paragraph(f'<b>{prediction}</b>', body_style)],
            [Paragraph('<b>Confidence Score:</b>', body_style), Paragraph(f'<b>{confidence}%</b>', body_style)]
        ]
        results_table = Table(results_data, colWidths=[2*inch, 4.5*inch])
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0F9FF')),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('BACKGROUND', (1, 1), (1, 1), result_color),  # Highlight prediction
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BFDBFE')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        story.append(results_table)
        story.append(Spacer(1, 0.4*inch))
        
        # Brain Scan Image Section
        if image_path:
            story.append(Paragraph("🖼️ Brain Scan Image", section_heading_style))
            story.append(Spacer(1, 0.15*inch))
            try:
                # Extract filename from URL path if needed (e.g., /static/uploads/file.jpg -> file.jpg)
                if image_path.startswith('/static/uploads/'):
                    filename = image_path.replace('/static/uploads/', '')
                    img_full_path = os.path.join(UPLOAD_FOLDER, filename)
                elif image_path.startswith('static/uploads/'):
                    filename = image_path.replace('static/uploads/', '')
                    img_full_path = os.path.join(UPLOAD_FOLDER, filename)
                else:
                    # Assume it's just the filename
                    img_full_path = os.path.join(UPLOAD_FOLDER, image_path)
                
                print(f"DEBUG: Looking for image at: {img_full_path}")  # Debug logging
                
                if os.path.exists(img_full_path):
                    # Create a bordered image container
                    img = RLImage(img_full_path, width=4*inch, height=4*inch)
                    img_data = [[img]]
                    img_table = Table(img_data, colWidths=[4*inch])
                    img_table.setStyle(TableStyle([
                        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#3B82F6')),
                        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 10),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                        ('TOPPADDING', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ]))
                    story.append(img_table)
                    story.append(Spacer(1, 0.4*inch))
                else:
                    print(f"DEBUG: Image file not found at: {img_full_path}")  # Debug logging
                    story.append(Paragraph(f"<i>Image file not found at expected location</i>", body_style))
                    story.append(Spacer(1, 0.3*inch))
            except Exception as e:
                print(f"DEBUG: Error loading image: {str(e)}")  # Debug logging
                story.append(Paragraph(f"<i>Image could not be loaded: {str(e)}</i>", body_style))
                story.append(Spacer(1, 0.3*inch))
        
        # Result Analysis Section
        story.append(Paragraph("📊 Result Analysis", section_heading_style))
        story.append(Spacer(1, 0.15*inch))
        
        # Generate analysis based on confidence
        try:
            conf_value = float(confidence.strip('%')) if isinstance(confidence, str) else confidence
        except:
            conf_value = 0
        
        # Confidence interpretation with color coding
        if conf_value >= 90:
            conf_interpretation = "Very High - The model is highly confident in this prediction."
            conf_color = colors.HexColor('#D1FAE5')
        elif conf_value >= 75:
            conf_interpretation = "High - The model shows strong confidence in this prediction."
            conf_color = colors.HexColor('#DBEAFE')
        elif conf_value >= 60:
            conf_interpretation = "Moderate - The model shows reasonable confidence, but further clinical evaluation is recommended."
            conf_color = colors.HexColor('#FEF3C7')
        else:
            conf_interpretation = "Low - The model has limited confidence. Additional testing is strongly recommended."
            conf_color = colors.HexColor('#FEE2E2')
        
        # Confidence level box
        conf_data = [[Paragraph(f'<b>Confidence Level:</b> {conf_interpretation}', body_style)]]
        conf_table = Table(conf_data, colWidths=[6.5*inch])
        conf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), conf_color),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#94A3B8')),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(conf_table)
        story.append(Spacer(1, 0.25*inch))
        
        # Clinical Recommendations
        clinical_text = """
        <b>Clinical Recommendation:</b><br/><br/>
        This AI-assisted analysis should be used as a <b>supplementary diagnostic tool</b>. 
        The results must be reviewed and validated by qualified medical professionals. 
        Further clinical examination, additional imaging, and comprehensive patient history 
        should be considered before making any diagnostic or treatment decisions.
        """
        story.append(Paragraph(clinical_text, body_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Important Notes Box
        notes_text = """
        <b>⚠️ Important Notes:</b><br/>
        • This is an AI-generated prediction and not a definitive diagnosis<br/>
        • Results should be interpreted by qualified healthcare professionals<br/>
        • Additional tests may be required for confirmation<br/>
        • Patient symptoms and medical history must be considered<br/>
        • This report is for medical professional use only
        """
        notes_data = [[Paragraph(notes_text, body_style)]]
        notes_table = Table(notes_data, colWidths=[6.5*inch])
        notes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF3C7')),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#F59E0B')),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(notes_table)
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_line = Table([['']], colWidths=[6.5*inch])
        footer_line.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#CBD5E1')),
        ]))
        story.append(footer_line)
        story.append(Spacer(1, 0.15*inch))
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#64748B'),
            alignment=TA_CENTER
        )
        story.append(Paragraph("<b>NeuroSight</b> - AI-Powered Brain Disease Detection", footer_style))
        story.append(Paragraph("Rajalakshmi Engineering College, Thandalam, Chennai", footer_style))
        story.append(Paragraph("Contact: asuproject0112@gmail.com", footer_style))
        
        doc.build(story)
        
        return send_file(pdf_path, as_attachment=True, download_name=pdf_filename, mimetype='application/pdf')
    
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'danger')
        return redirect(url_for('detect'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✓ Database initialized")
        
    # Get local IP address to show the user
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"\n🚀 App is running! Access it from other devices on your network at:")
        print(f"👉 http://{local_ip}:5000")
    except:
        print("\n🚀 App is running on localhost")
    
    # host='0.0.0.0' allows access from other devices on the network
    app.run(debug=True, host='0.0.0.0', port=5000)
