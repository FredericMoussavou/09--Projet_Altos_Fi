import json
import os
from sqlalchemy.orm import Session
from app.models.user import Category, Pocket, Transaction

def classify_transaction(db: Session, user_id: str, label: str):
    """
    Parcourt le dictionnaire d'apprentissage pour trouver une catégorie 
    correspondant au libellé bancaire.
    """
    file_path = os.path.join("app", "core", "settings.json")
    
    if not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        settings = json.load(f)
    
    label_upper = label.upper()
    
    for keyword, target_cat_name in settings["mappings"].items():
        if keyword.upper() in label_upper:
            # Recherche de la catégorie correspondante chez cet utilisateur
            category = db.query(Category).join(Pocket).filter(
                Pocket.user_id == user_id,
                Category.name == target_cat_name
            ).first()
            
            if category:
                return category.id # On retourne l'ID pour la transaction
    
    return None

def reclassify_and_learn(db: Session, transaction_id: str, new_category_id: str, keyword: str):
    # 1. Récupérer la transaction
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        return False

    # 2. Récupérer la nouvelle catégorie pour connaître son nom
    new_cat = db.query(Category).filter(Category.id == new_category_id).first()
    
    # 3. Mettre à jour le JSON d'apprentissage
    file_path = os.path.join("app", "core", "settings.json")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # On ajoute la nouvelle règle (ex: "PATISSERIE": "Restauration")
    data["mappings"][keyword.upper()] = new_cat.name
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # 4. Mettre à jour la transaction en base
    tx.category_id = new_category_id
    db.commit()
    
    return True