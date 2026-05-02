import json
import os
import bcrypt
from itsdangerous import URLSafeTimedSerializer
from django.conf import settings
import resend

SECRET_KEY = settings.SECRET_KEY
serializer = URLSafeTimedSerializer(SECRET_KEY)
ADMIN_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "login-data", "admin.json"
)

def hash_password(password: str) -> str:
    """Hash le mot de passe en utilisant bcrypt avec un salt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def load_admin_data() -> dict:
    """Charge les informations de l'administrateur depuis le fichier json."""
    with open(ADMIN_DATA_PATH, 'r') as f:
        return json.load(f)
    
def verify_admin_credentials(email: str, password: str) -> bool:
    """Vérifie les identifiants de l'administrateur."""
    try:
        admin_data = load_admin_data()
        if email != admin_data.get("email"):
            return False
            
        stored_hash = admin_data.get("password", "")
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    except (FileNotFoundError, KeyError, ValueError):
        return False

def verify_admin_password(password: str) -> bool:
    """Vérifie si le mot de passe fourni correspond à celui de l'administrateur."""
    try:
        admin_data = load_admin_data()
        stored_hash = admin_data.get("password", "")
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    except (FileNotFoundError, KeyError, ValueError):
        return False
    
def update_admin_credentials(email: str, password: str) -> None:
    """Met à jour les identifiants de l'administrateur dans le fichier JSON."""
    try:
        admin_data = load_admin_data()
        admin_data["email"] = email
        admin_data["password"] = hash_password(password)

        with open(ADMIN_DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(admin_data, f, indent=2)
        return True
    except Exception:
        return False
    
def is_admin_logged_in(request) -> bool:
    """Vérifie si l'administrateur est connecté en vérifiant la session."""
    return request.session.get("admin_logged_in", False)

def admin_login_session(request) -> None:
    """Démarre une session pour l'administrateur après une connexion réussie."""
    request.session["admin_logged_in"] = True

def admin_logout_session(request) -> None:
    """Termine la session de l'administrateur lors de la déconnexion."""
    request.session.flush()

def generate_reset_token(email: str) -> str:
    return serializer.dumps(email, salt='reset-password')

def verify_reset_token(token: str, expiration=3600) -> str:
    try:
        email = serializer.loads(
            token, 
            salt='reset-password', 
            max_age=expiration
        )
        return email
    except Exception:
        return None
    
def send_password_reset_email(email: str, token: str) -> bool:
    """Envoie un email de réinitialisation de mot de passe via Resend."""
    try:
        # Initialiser le client Resend
        resend.api_key = settings.RESEND_API_KEY
        
        if not settings.RESEND_API_KEY:
            print("Error: RESEND_API_KEY is not configured")
            return False
        
        reset_link = f"https://predictpriceai-backend-production.up.railway.app/reset-password?token={token}"
        
        # Envoyer l'email avec Resend
        email_response = resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": email,
            "subject": "Password Reset Request - PredictPrice AI",
            "html": f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
                            <h2>Password Reset Request</h2>
                            <p>You have requested to reset your password for your PredictPrice AI account.</p>
                            <p>Click the link below to reset your password:</p>
                            <p style="margin: 20px 0;">
                                <a href="{reset_link}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">
                                    Reset Password
                                </a>
                            </p>
                            <p>Or copy and paste this link in your browser:</p>
                            <p style="word-break: break-all; color: #666;">{reset_link}</p>
                            <p style="margin-top: 20px; font-size: 12px; color: #999;">
                                This link will expire in 1 hour.<br>
                                If you did not request a password reset, please ignore this email.
                            </p>
                        </div>
                    </body>
                </html>
            """
        })
        
        if email_response.get("id"):
            print(f"Password reset email sent successfully to {email}")
            return True
        else:
            print(f"Error sending password reset email: {email_response}")
            return False
            
    except Exception as e:
        print(f"Error sending password reset email: {str(e)}")
        return False