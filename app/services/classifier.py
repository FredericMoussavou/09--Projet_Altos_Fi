import json
import os
from sqlalchemy.orm import Session
from app.models.user import Category, Pocket
from sqlalchemy import func, or_

SETTINGS_PATH = os.path.join("app", "core", "settings.json")

def get_all_mappings():
    """Charge les mots-clés depuis le fichier settings.json."""
    if not os.path.exists(SETTINGS_PATH):
        return {}
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("learning_mappings", {})

def get_category_id_by_name(db: Session, user_id: str, category_name: str):
    """Retrouve l'ID d'une catégorie (Renvoie un string ou None)."""
    # .scalar() renvoie directement la valeur de la colonne Category.id
    return db.query(Category.id).join(Pocket).filter(
        Pocket.user_id == user_id,
        or_(
            func.lower(Category.name) == category_name.lower(),
            func.lower(Category.name) == "à classer",
            func.lower(Category.name) == "a classer"
        )
    ).scalar()

def classify_transaction(db: Session, user_id: str, label: str):
    mappings = get_all_mappings()
    clean_label = label.upper().strip() if label else ""
    
    # 1. Tentative avec les mots-clés
    sorted_keywords = sorted(mappings.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        if keyword.upper() in clean_label:
            target_cat_name = mappings[keyword]
            cat_id = get_category_id_by_name(db, user_id, target_cat_name)
            if cat_id:
                return cat_id

    # 2. Fallback vers "À classer"
    # .scalar() ici aussi pour garantir qu'on récupère le string de l'ID
    fallback_id = db.query(Category.id).join(Pocket).filter(
        Pocket.user_id == user_id,
        func.lower(Pocket.name).contains("classer")
    ).scalar()
    
    return fallback_id

def classify_transaction(db: Session, user_id: str, label: str):
    mappings = get_all_mappings()
    clean_label = label.upper().strip() if label else ""
    
    # 1. Tentative avec les mappings
    sorted_keywords = sorted(mappings.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        if keyword.upper() in clean_label:
            target_cat_name = mappings[keyword]
            cat_id = get_category_id_by_name(db, user_id, target_cat_name)
            if cat_id:
                return cat_id

    fallback = db.query(Category.id).join(Pocket).filter(
        Pocket.user_id == user_id,
        func.lower(Pocket.name).contains("classer")
    ).first()
    
    return fallback[0] if fallback else None

def reclassify_and_learn(db: Session, label: str, new_category_name: str):
    """
    Apprend un nouveau mapping à partir d'une correction utilisateur.
    Extraie un mot-clé significatif du libellé et l'ajoute au settings.json.
    """
    if not label or not new_category_name:
        return False

    # 1. Nettoyage du libellé pour extraire un mot-clé (on prend les 2 premiers mots par ex)
    # Ou on peut prendre le libellé complet s'il est court
    words = label.upper().split()
    keyword = " ".join(words[:3]) if len(words) > 2 else label.upper()
    keyword = keyword.strip("!@#$%^&*()_+-=") # Nettoyage des caractères spéciaux

    # 2. Chargement du fichier actuel
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"learning_mappings": {}}

    # 3. Mise à jour du dictionnaire
    # On ajoute le nouveau mapping ou on met à jour l'existant
    data["learning_mappings"][keyword] = new_category_name

    # 4. Sauvegarde persistante
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erreur lors de l'apprentissage : {e}")
        return False