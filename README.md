# NeuroSight - AI-Powered Brain Disease Detection

🧠 **NeuroSight** is an advanced AI-powered platform for detecting brain diseases including Alzheimer's, Dementia, Multiple Sclerosis, and Stroke using deep learning models.

## 🌟 Features

- **Multi-Disease Detection**: Alzheimer's, Dementia, Multiple Sclerosis, Stroke
- **AI-Powered Analysis**: State-of-the-art deep learning models
- **User Authentication**: 
  - Google OAuth integration
  - Email/Password with OTP verification
- **Professional Onboarding**: Doctor credentials and hospital information
- **Scan History**: Track and review previous diagnoses
- **PDF Reports**: Generate detailed medical reports
- **Secure & Compliant**: Email verification, secure authentication

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd "final year aiml project"
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `config.py` file with:
   ```python
   # Email Configuration
   MAIL_SERVER = 'smtp.gmail.com'
   MAIL_PORT = 587
   MAIL_USERNAME = 'your-email@gmail.com'
   MAIL_PASSWORD = 'your-app-password'
   
   # Google OAuth
   GOOGLE_CLIENT_ID = 'your-client-id'
   GOOGLE_CLIENT_SECRET = 'your-client-secret'
   ```

5. **Download AI Models**
   Due to file size limitations, AI models are not included in the repository.
   Download from [Google Drive/OneDrive link] and place in project root:
   - `alzhimermodel.pth`
   - `dementia_detection_model_2.h5`
   - `multiple_sclerosis.pth`
   - `stroke.pth`

6. **Run the application**
   ```bash
   python neurosight_app_with_auth.py
   ```

7. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## 📁 Project Structure

```
final year aiml project/
├── neurosight_app_with_auth.py  # Main application
├── models.py                     # Database models
├── auth_utils.py                 # Authentication utilities
├── requirements.txt              # Python dependencies
├── templates/                    # HTML templates
│   ├── login.html
│   ├── register.html
│   ├── verify_email.html
│   ├── dashboard.html
│   ├── detect.html
│   └── ...
├── static/                       # Static assets
│   ├── css/
│   ├── js/
│   └── images/
└── instance/                     # Database files
```

## 🔐 Authentication Flow

### Email/Password Registration
1. User registers with email and password
2. System sends 6-digit OTP to email
3. User verifies OTP
4. User completes onboarding
5. Access granted to dashboard

### Google OAuth
1. User clicks "Continue with Google"
2. Google authentication
3. User completes onboarding (if first time)
4. Access granted to dashboard

## 🧪 Testing

### Email System
```bash
python test_email.py
```

### Database Management
```bash
python db_manager.py
```

## 📧 Email Configuration

The application uses Gmail SMTP for sending emails:
- OTP verification codes
- Welcome emails
- Password reset emails

**Setup Gmail App Password:**
1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password
3. Use the App Password in `config.py`

## 🛠️ Database Management

### View Database
```bash
python view_db.py
```

### Manage Users
```bash
python db_manager.py
```

### Run Migrations
```bash
python migrate_otp_fields.py
```

## 🔒 Security Features

- ✅ OTP email verification (10-minute expiry)
- ✅ Password strength validation
- ✅ Attempt limiting (5 max OTP attempts)
- ✅ TLS email encryption
- ✅ Secure session management
- ✅ Google OAuth integration

## 📊 Supported Diseases

1. **Alzheimer's Disease**
2. **Dementia**
3. **Multiple Sclerosis**
4. **Stroke**

## 🤝 Contributing

This is a final year AIML project. For questions or contributions, please contact the project team.

## 📄 License

See LICENSE file for details.

## 👥 Team

Final Year AIML Project Team

## 📞 Support

For issues or questions:
- Check the documentation
- Review the walkthrough guides
- Contact the development team

---

**Built with ❤️ using Flask, TensorFlow, and modern web technologies**
