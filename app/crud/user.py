import json
import os
from sqlalchemy.orm import Session
from app.models.user import User, UserSettings, Pocket, Category
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

DEFAULTS_PATH = os.path.join("app", "core", "defaults.json")

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    """
    Crée un utilisateur et initialise ses Pockets à partir de la structure
    system_pockets et user_pockets du fichier defaults.json.
    """
    # 1. Sécurité & Création User
    hashed_pwd = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pwd,
        first_name=user.first_name,
        last_name=user.last_name
    )
    db.add(db_user)
    db.flush() 

    # 2. Réglages (Dîme désactivée par défaut)
    user_settings = UserSettings(user_id=db_user.id, tithing_enabled=False)
    db.add(user_settings)

    # 3. Création des Pockets via defaults.json
    if os.path.exists(DEFAULTS_PATH):
        with open(DEFAULTS_PATH, "r", encoding="utf-8") as f:
            defaults = json.load(f)
        
        # On fusionne les deux listes du JSON pour les traiter
        all_pockets_data = defaults.get("system_pockets", []) + defaults.get("user_pockets", [])
        
        for p_data in all_pockets_data:
            new_pocket = Pocket(name=p_data["name"], user_id=db_user.id)
            db.add(new_pocket)
            db.flush()
            
            # Ajout des catégories
            for cat_name in p_data.get("categories", []):
                new_cat = Category(name=cat_name, pocket_id=new_pocket.id)
                db.add(new_cat)
    
    db.commit()
    db.refresh(db_user)
    return db_user