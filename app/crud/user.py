import bcrypt
import json
import os
from sqlalchemy.orm import Session
from app.models.user import User, Profile, UserPreferences, Pocket, Category
from app.schemas.user import UserCreate

# --- SÉCURITÉ ---
def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# --- CHARGEMENT DES PARAMÈTRES EXTERNALISÉS ---
def load_defaults():
    # Chemin vers le fichier JSON
    file_path = os.path.join("app", "core", "defaults.json")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- RECHERCHE ---
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# --- CRÉATION & INITIALISATION ---
def create_user(db: Session, user_in: UserCreate):
    hashed_password = get_password_hash(user_in.password)
    defaults = load_defaults()
    
    # 1. Création de l'User
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hashed_password,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        gender=user_in.gender
    )
    db.add(db_user)
    db.flush() 

    # 2. Profil et Préférences
    db.add(Profile(user_id=db_user.id))
    db.add(UserPreferences(user_id=db_user.id))

    # 3. INITIALISATION DEPUIS LE JSON
    # On traite les pockets système ET utilisateur de la même manière via le JSON
    all_pockets = defaults["system_pockets"] + defaults["user_pockets"]

    for pkt_data in all_pockets:
        new_pkt = Pocket(
            user_id=db_user.id, 
            name=pkt_data["name"], 
            is_system=pkt_data["is_system"]
        )
        db.add(new_pkt)
        db.flush()
        
        for cat_name in pkt_data["categories"]:
            db.add(Category(pocket_id=new_pkt.id, name=cat_name))

    db.commit()
    db.refresh(db_user)
    return db_user

def create_pocket(db: Session, user_id: str, name: str):
    # 1. Charger la limite depuis settings.json
    with open("app/core/settings.json") as f:
        settings = json.load(f)
    
    # 2. Compter les pockets actuelles de l'utilisateur (hors système)
    count = db.query(Pocket).filter(
        Pocket.user_id == user_id, 
        Pocket.is_system == False
    ).count()
    
    # 3. Vérification de la limite
    if count >= settings["max_user_pockets"]:
        raise Exception(f"Limite de {settings['max_user_pockets']} pockets atteinte.")
    
    # 4. Création si OK
    new_pocket = Pocket(user_id=user_id, name=name, is_system=False)
    db.add(new_pocket)
    db.commit()
    return new_pocket