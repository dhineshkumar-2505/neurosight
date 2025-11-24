"""
Database models for NeuroSight authentication system
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for doctors and radiologists"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for OAuth users
    full_name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'doctor' or 'radiologist'
    hospital = db.Column(db.String(255))
    license_number = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # OAuth fields
    google_id = db.Column(db.String(255), unique=True, index=True)
    profile_photo_url = db.Column(db.String(500))
    
    # Password reset fields
    reset_token = db.Column(db.String(255))
    reset_token_expiry = db.Column(db.DateTime)
    
    # Doctor Details (for onboarding)
    medical_registration_no = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    years_of_experience = db.Column(db.Integer)
    clinic_timing = db.Column(db.String(255))
    
    # Hospital Details (for onboarding)
    hospital_id = db.Column(db.String(100))
    hospital_address = db.Column(db.Text)
    department = db.Column(db.String(100))
    hospital_logo_url = db.Column(db.String(500))
    hospital_phone = db.Column(db.String(20))
    
    # Onboarding tracking
    onboarding_completed = db.Column(db.Boolean, default=False)
    
    # Email verification with OTP
    email_verified = db.Column(db.Boolean, default=False)
    otp_code = db.Column(db.String(6))
    otp_expiry = db.Column(db.DateTime)
    otp_attempts = db.Column(db.Integer, default=0)

    
    # Relationships
    analyses = db.relationship('AnalysisHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def generate_reset_token(self):
        """Generate a secure password reset token"""
        self.reset_token = secrets.token_urlsafe(32)
        return self.reset_token
    
    def generate_otp(self):
        """Generate a 6-digit OTP for email verification"""
        import random
        from datetime import datetime, timedelta
        
        self.otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.otp_expiry = datetime.utcnow() + timedelta(minutes=10)  # OTP valid for 10 minutes
        self.otp_attempts = 0
        return self.otp_code
    
    def verify_otp(self, otp):
        """Verify the OTP code"""
        from datetime import datetime
        
        # Check if OTP exists
        if not self.otp_code:
            return False, "No OTP generated"
        
        # Check if OTP has expired
        if datetime.utcnow() > self.otp_expiry:
            return False, "OTP has expired"
        
        # Check attempt limit (max 5 attempts)
        if self.otp_attempts >= 5:
            return False, "Too many failed attempts. Please request a new OTP"
        
        # Verify OTP
        if self.otp_code == otp:
            self.email_verified = True
            self.otp_code = None
            self.otp_expiry = None
            self.otp_attempts = 0
            return True, "Email verified successfully"
        else:
            self.otp_attempts += 1
            remaining = 5 - self.otp_attempts
            return False, f"Invalid OTP. {remaining} attempts remaining"

    
    def needs_onboarding(self):
        """Check if user needs to complete onboarding"""
        return not self.onboarding_completed
    
    def has_required_doctor_details(self):
        """Check if user has all required doctor details"""
        return all([
            self.full_name,
            self.medical_registration_no,
            self.specialization,
            self.phone,
            self.email,
            self.years_of_experience is not None
        ])
    
    def has_required_hospital_details(self):
        """Check if user has all required hospital details"""
        return all([
            self.hospital,
            self.hospital_id,
            self.department
        ])
    
    def can_complete_onboarding(self):
        """Check if user can complete onboarding (all required fields filled)"""
        return self.has_required_doctor_details() and self.has_required_hospital_details()
    
    def __repr__(self):
        return f'<User {self.email}>'


class AnalysisHistory(db.Model):
    """Analysis history for tracking patient scans"""
    __tablename__ = 'analysis_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Patient information
    patient_name = db.Column(db.String(255))
    patient_id = db.Column(db.String(100))
    patient_age = db.Column(db.Integer)
    scan_date = db.Column(db.Date)
    
    # Analysis results
    disease_type = db.Column(db.String(50), nullable=False)  # 'ms', 'alzheimer', 'dementia', 'stroke'
    prediction = db.Column(db.String(255), nullable=False)
    confidence = db.Column(db.Float)
    
    # File paths
    image_path = db.Column(db.String(500))
    report_path = db.Column(db.String(500))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    notes = db.Column(db.Text)  # Doctor's notes
    
    def __repr__(self):
        return f'<Analysis {self.id} - {self.disease_type}>'


def init_db(app):
    """Initialize database"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("✓ Database tables created successfully")
