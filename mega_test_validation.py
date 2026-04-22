from app.core.database import SessionLocal, engine, Base
from app.crud.user import create_user
from app.schemas.user import UserCreate
from app.models.user import User, Pocket, Category, Transaction
from app.services.classifier import classify_transaction, reclassify_and_learn
from pydantic import ValidationError
import json
import os

# Préparation : Base propre
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
db = SessionLocal()

print("🚀 DÉMARRAGE DU MÉGA TEST ALTOS FI (Version Sécurité)\n")

try:
    # --- SCÉNARIO 0 : SÉCURITÉ ET ROBUSTESSE ---
    print("--- Scénario 0 : Tests de rejets (Erreurs attendues) ---")
    
    # Test A : Mot de passe trop court
    try:
        UserCreate(
            username="mauvais_mdp",
            email="bad_pwd@altos.fi",
            password="123", # Trop court
            first_name="Test",
            last_name="Mdp"
        )
        print("❌ ERREUR : Le système a accepté un mot de passe trop court !")
    except ValidationError:
        print("✅ RÈGLE : Mot de passe trop court rejeté (Pydantic).")

    # Test B : Username incorrect (ex: vide)
    try:
        UserCreate(
            username="", # Vide
            email="bad_user@altos.fi",
            password="CyberPassword123!",
            first_name="Test",
            last_name="User"
        )
        print("❌ ERREUR : Le système a accepté un username vide !")
    except ValidationError:
        print("✅ RÈGLE : Username vide rejeté.")

    # Test C : Email invalide
    try:
        UserCreate(
            username="bad_email",
            email="pas-un-email",
            password="CyberPassword123!",
            first_name="Test",
            last_name="Email"
        )
        print("❌ ERREUR : Le système a accepté un email invalide !")
    except ValidationError:
        print("✅ RÈGLE : Email mal formé rejeté.")


    # --- SCÉNARIO 1 : AUTH & INITIALISATION (Le "Bon" utilisateur) ---
    print("\n--- Scénario 1 : Création Utilisateur Valide ---")
    user_in = UserCreate(
        username="altos_expert",
        email="expert@altos.fi",
        password="CyberPassword123!",
        first_name="Admin",
        last_name="Altos"
    )
    user = create_user(db, user_in)
    print(f"✅ Utilisateur '{user.username}' créé avec succès.")
    
    pockets = db.query(Pocket).filter(Pocket.user_id == user.id).all()
    pocket_names = [p.name for p in pockets]
    if "Dîme" in pocket_names and "À classer" in pocket_names:
        print(f"✅ Pockets systèmes présentes : {pocket_names}")
    else:
        print(f"❌ ERREUR : Pockets systèmes manquantes.")


    # --- SCÉNARIO 2 : LECTURE CONFIGURATION ---
    print("\n--- Scénario 2 : Vérification du Cerveau (settings.json) ---")
    with open("app/core/settings.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    print(f"✅ Ratio Dîme : {config['tithing']['default_ratio']}")
    print(f"✅ Nombre de mappings : {len(config['learning_mappings'])}")


    # --- SCÉNARIO 3 : CLASSIFICATION AUTOMATIQUE ---
    print("\n--- Scénario 3 : Test du Moteur de Tri ---")
    # On utilise des mots-clés présents dans ton settings.json
    tx_loyer_cat_id = classify_transaction(db, user.id, "LOYER JANVIER")
    tx_zara_cat_id = classify_transaction(db, user.id, "ACHAT ZARA") # Normalement inconnu
    
    if tx_loyer_cat_id:
        cat = db.query(Category).filter(Category.id == tx_loyer_cat_id).first()
        print(f"✅ 'LOYER JANVIER' -> {cat.name}")
    else:
        print("⚠️ 'LOYER' non classé automatiquement.")

    if tx_zara_cat_id is None:
        print("✅ 'ACHAT ZARA' est inconnu (Normal).")


# --- SCÉNARIO 4 : BOUCLE D'APPRENTISSAGE ---
    print("\n--- Scénario 4 : Apprentissage de l'IA ---")
    
    # Correction de la recherche : on cherche la catégorie dans la pocket "À classer"
    # Ou on cherche simplement une catégorie qui s'appelle "À classer"
    cat_a_classer = db.query(Category).filter(Category.name == "À classer").first()
    
    if not cat_a_classer:
        # Si elle n'existe pas, on regarde dans la Pocket "À classer" 
        # s'il y a une catégorie par défaut (souvent nommée "Divers" ou identique à la pocket)
        pocket_a_classer = db.query(Pocket).filter(Pocket.name == "À classer", Pocket.user_id == user.id).first()
        if pocket_a_classer and pocket_a_classer.categories:
            cat_a_classer = pocket_a_classer.categories[0]

    if not cat_a_classer:
        print("❌ ERREUR : Impossible de trouver une catégorie pour le tri par défaut.")
        raise Exception("Catégorie 'À classer' manquante dans la structure initiale.")

    # Création de la transaction Zara dans "À classer"
    new_tx = Transaction(
        user_id=user.id,
        category_id=cat_a_classer.id,
        label="ACHAT ZARA",
        amount=-45.0
    )
    db.add(new_tx)
    db.commit()
    
    # On vérifie aussi que "Loisirs" existe bien (Attention aux accents/majuscules)
    cat_loisirs = db.query(Category).filter(Category.name == "Loisirs").first()
    if not cat_loisirs:
        # On essaie "Habillement" ou une autre catégorie de ton defaults.json si Loisirs n'existe pas
        cat_loisirs = db.query(Category).first() # On prend la première disponible pour le test

    # --- SCÉNARIO 5 : IDENTIFICATION REVENUS ---
    print("\n--- Scénario 5 : Identification des flux entrants ---")
    tx_sal_id = classify_transaction(db, user.id, "VERS SALAIRE")
    if tx_sal_id:
        cat_sal = db.query(Category).filter(Category.id == tx_sal_id).first()
        print(f"✅ Revenu détecté : {cat_sal.name}")

except Exception as e:
    print(f"\n💥 CRASH INATTENDU : {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
    print("\n--- FIN DU MÉGA TEST ---")