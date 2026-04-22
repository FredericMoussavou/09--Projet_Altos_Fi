import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie le mot de passe. 
    bcrypt gère automatiquement l'extraction du sel depuis le hash.
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def get_password_hash(password: str) -> str:
    """
    Génère un sel et hache le mot de passe.
    Retourne le hash sous forme de chaîne de caractères (compatible SQLite/Postgres).
    """
    # bcrypt nécessite des bytes en entrée
    password_bytes = password.encode('utf-8')
    
    # Génération du sel et du hash (12 rounds est le standard actuel)
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # On décode en string pour le stockage en base
    return hashed.decode('utf-8')