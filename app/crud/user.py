# app/crud/user.py
import bcrypt
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate

def get_password_hash(password: str) -> str:
    """ Transforme le mot de passe clair en hash sécurisé avec bcrypt. """
    # 1. On génère un 'salt' (sel) aléatoire pour renforcer la sécurité
    salt = bcrypt.gensalt()
    # 2. On hache le mot de passe (il doit être encodé en bytes)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    # 3. On retourne le résultat sous forme de chaîne de caractères (string)
    return hashed.decode('utf-8')

def create_user(db: Session, user_in: UserCreate):
    """ Enregistre un utilisateur avec son mot de passe haché proprement. """
    
    hashed_password = get_password_hash(user_in.password)
    
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hashed_password,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        is_dime_enabled=user_in.is_dime_enabled,
        gender=user_in.gender
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def get_user_by_email(db: Session, email: str):
    """Cherche un utilisateur dans la base via son email."""
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str):
    """Cherche un utilisateur par son nom d'utilisateur."""
    return db.query(User).filter(User.username == username).first()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe tapé correspond au hash en base."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def update_user_password(db: Session, user: User, new_password: str):
    """Met à jour le mot de passe d'un utilisateur avec un nouveau hash."""
    user.password_hash = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user