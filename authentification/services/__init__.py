import json
import os
import bcrypt
from threading import Thread
from itsdangerous import URLSafeTimedSerializer
from django.conf import settings
from django.core.mail import send_mail

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
    """
    Envoie un email de réinitialisation de mot de passe de manière asynchrone.
    
    Cette fonction lance l'envoi d'email dans un thread séparé et retourne
    immédiatement, sans bloquer la requête HTTP.
    
    Args:
        email: Email de l'administrateur
        token: Token de réinitialisation
    
    Returns:
        bool: True si la tâche a été lancée avec succès
    """
    def send_async():
        """Envoie l'email dans un thread séparé via Gmail SMTP."""
        try:
            # Vérifier que les paramètres SMTP sont configurés
            if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
                print("ERROR: EMAIL_HOST_USER or EMAIL_HOST_PASSWORD not configured")
                print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
                print(f"EMAIL_HOST_PASSWORD: {'*' * 5 if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
                return False
            
            reset_link = f"https://predictpriceai-backend-production.up.railway.app/reset-password?token={token}"
            subject = "Password Reset Request - PredictPrice AI"
            message = f"""
            Click the link below to reset your password:
            
            {reset_link}
            
            This link will expire in 1 hour.
            
            If you did not request a password reset, please ignore this email.
            """
            
            html_message = f"""
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
            
            print(f"Attempting to send password reset email to {email}")
            print(f"SMTP Configuration: HOST={settings.EMAIL_HOST}:{settings.EMAIL_PORT}, USE_SSL={settings.EMAIL_USE_SSL}, USE_TLS={settings.EMAIL_USE_TLS}")
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
                html_message=html_message
            )
            print(f"Password reset email sent successfully to {email}")
        except Exception as e:
            import traceback
            print(f"Error sending password reset email: {str(e)}")
            print(f"Exception type: {type(e).__name__}")
            print(f"Traceback: {traceback.format_exc()}")
    
    try:
        # Lancer l'envoi d'email dans un thread démon
        thread = Thread(target=send_async, daemon=True)
        thread.start()
        return True
    except Exception as e:
        import traceback
        print(f"Error creating email thread: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return False