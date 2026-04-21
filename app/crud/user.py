import bcrypt
from sqlalchemy.orm import Session
from app.models.user import User, Profile, UserPreferences
from app.schemas.user import UserCreate

# --- SÉCURITÉ ---

def get_password_hash(password: str) -> str:
    """ Transforme le mot de passe clair en hash sécurisé avec bcrypt. """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """ Vérifie si le mot de passe tapé correspond au hash en base. """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- RECHERCHE ---

def get_user(db: Session, user_id: str):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

# --- CRÉATION ---

def create_user(db: Session, user_in: UserCreate):
    """ 
    Enregistre un utilisateur et initialise automatiquement 
    son profil et ses préférences budgétaires. 
    """
    hashed_password = get_password_hash(user_in.password)
    
    # 1. Création de l'entrée principale User
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hashed_password,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        gender=user_in.gender,
        is_active=True,
        is_premium=False
    )
    
    db.add(db_user)
    db.flush()  # Récupère l'ID généré pour les relations suivantes sans clore la transaction

    # 2. Création du profil (vide par défaut)
    db_profile = Profile(user_id=db_user.id)
    db.add(db_profile)

    # 3. Création des préférences (ratios 50/30/20/0 par défaut)
    db_prefs = UserPreferences(user_id=db_user.id)
    db.add(db_prefs)

    # 4. Validation finale de la "triplette"
    db.commit()
    db.refresh(db_user)
    
    return db_user

# --- MISE À JOUR ---

def update_user_password(db: Session, user: User, new_password: str):
    user.password_hash = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user