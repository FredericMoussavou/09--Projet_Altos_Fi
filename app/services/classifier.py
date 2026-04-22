import json
import os
from sqlalchemy.orm import Session
from app.models.user import Category, Pocket, Transaction

# Chemin centralisé
SETTINGS_PATH = os.path.join("app", "core", "settings.json")

def classify_transaction(db: Session, user_id: str, label: str):
    """
    Parcourt le dictionnaire d'apprentissage (settings.json) pour trouver 
    une catégorie correspondant au libellé bancaire.
    """
    if not os.path.exists(SETTINGS_PATH):
        return None

    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        settings = json.load(f)
    
    # Utilisation de la nouvelle clé consolidée
    mappings = settings.get("learning_mappings", {})
    label_upper = label.upper()
    
    for keyword, target_cat_name in mappings.items():
        if keyword.upper() in label_upper:
            # Recherche de la catégorie correspondante chez cet utilisateur
            category = db.query(Category).join(Pocket).filter(
                Pocket.user_id == user_id,
                Category.name == target_cat_name
            ).first()
            
            if category:
                return category.id
    
    return None

def reclassify_and_learn(db: Session, transaction_id: str, new_category_id: str, keyword: str):
    """
    Met à jour une transaction, identifie un nouveau mot-clé et 
    l'enregistre dans les mappings globaux.
    """
    # 1. Récupérer la transaction
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        return False

    # 2. Récupérer la nouvelle catégorie pour connaître son nom
    new_cat = db.query(Category).filter(Category.id == new_category_id).first()
    if not new_cat:
        return False
    
    # 3. Mettre à jour le JSON (settings.json)
    if not os.path.exists(SETTINGS_PATH):
        return False

    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Sécurité : On s'assure que la clé existe avant d'écrire
    if "learning_mappings" not in data:
        data["learning_mappings"] = {}

    # On ajoute/met à jour la règle
    data["learning_mappings"][keyword.upper()] = new_cat.name
    
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # 4. Mettre à jour la transaction en base
    tx.category_id = new_category_id
    db.commit()
    
    return True