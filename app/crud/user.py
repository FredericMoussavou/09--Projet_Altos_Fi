import json
import os
from sqlalchemy.orm import Session
from app.models.user import User, UserSettings, Pocket, Category
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

DEFAULTS_PATH = os.path.join("app", "core", "defaults.json")

def get_user_by_username(db: Session, username: str):
    """Récupère un utilisateur par son nom d'utilisateur."""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    """
    Crée un utilisateur et initialise ses Pockets et Catégories à partir de la structure
    enrichie (avec types Fixed/Variable) du fichier defaults.json.
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
    user_settings = UserSettings(
        user_id=db_user.id, 
        tithing_enabled=False,
        morning_briefing_enabled=True,
        instant_alerts_enabled=True,
        global_alert_threshold=0.15,
        lock_vases_communicants=True
    )
    db.add(user_settings)

    # 3. Création des Pockets et Catégories via defaults.json
    if os.path.exists(DEFAULTS_PATH):
        with open(DEFAULTS_PATH, "r", encoding="utf-8") as f:
            defaults = json.load(f)
        
        # On fusionne les system_pockets et user_pockets pour les traiter
        all_pockets_data = defaults.get("system_pockets", []) + defaults.get("user_pockets", [])
        
        for p_data in all_pockets_data:
            new_pocket = Pocket(
                name=p_data["name"],
                user_id=db_user.id
            )
            db.add(new_pocket)
            db.flush()  # Nécessaire pour obtenir l'ID de la pocket avant de créer les catégories

            # Création des catégories pour cette pocket
            for cat_data in p_data.get("categories", []):
                # cat_data est maintenant un dictionnaire : {"name": "...", "type": "..."}
                category_name = cat_data.get("name")
                # On récupère le type, on le met en majuscule pour correspondre à l'Enum (ex: "fixed" -> "FIXED")
                category_type = cat_data.get("type", "variable").upper()

                new_cat = Category(
                    name=category_name,
                    pocket_id=new_pocket.id,
                    type=category_type
                )
                db.add(new_cat)

    db.commit()
    db.refresh(db_user)
    return db_user