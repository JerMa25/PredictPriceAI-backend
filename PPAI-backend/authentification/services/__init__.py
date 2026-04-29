import email
import json
import os
import bcrypt

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