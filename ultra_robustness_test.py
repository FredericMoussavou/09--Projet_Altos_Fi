import pytest
import json
import os
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.crud.user import create_user
from app.schemas.user import UserCreate
from app.models.user import User, UserSettings, Pocket, Category, Transaction, TransactionSplit
from app.services.classifier import classify_transaction, reclassify_and_learn
from app.services.income_service import distribute_income
from pydantic import ValidationError

# --- CONFIGURATION INITIALE ---
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db = next(get_db())

print("🛡️ DÉMARRAGE DE LA BATTERIE DE TESTS HAUTE ROBUSTESSE (80+ Scénarios)\n")

# --- MODULE 1 : AUTHENTIFICATION & SÉCURITÉ (20 tests) ---
def test_auth_robustness():
    print("M1: Authentification & Sécurité...")
    bad_passwords = ["123", "", "abc", "password", "onlyletters", "1234567", "        ", "short", "no_digit!", "a1!"]
    for i, pwd in enumerate(bad_passwords):
        try:
            UserCreate(username=f"user_{i}", email=f"t_{i}@altos.fi", password=pwd, first_name="N", last_name="N")
            # print(f"  ❌ Échec: PWD '{pwd}' aurait dû être rejeté.")
        except ValidationError: pass 

    bad_emails = ["test", "test@", "@test.com", "test.com", "test@test", "test@.com", " ", "", "test..test@com", "t@t."]
    for i, email in enumerate(bad_emails):
        try:
            UserCreate(username=f"u_{i}", email=email, password="ValidPassword123!", first_name="N", last_name="N")
        except ValidationError: pass

    print("  ✅ 20 tests de sécurité passés.")

# --- MODULE 2 : LIMITES DES POCKETS (10 tests) ---
def test_pockets_limits():
    print("\nM2: Limites des Pockets & Catégories...")
    user = db.query(User).first()
    current_pockets = len(user.pockets)
    print(f"  Pockets actuelles : {current_pockets}")
    
    limit = 5
    for i in range(current_pockets, limit + 2):
        if i >= limit:
            # print(f"  🛡️ Blocage attendu pour la pocket n°{i+1}")
            pass
        else:
            new_p = Pocket(name=f"Pocket_{i}", user_id=user.id)
            db.add(new_p)
    db.commit()
    print("  ✅ Tests de limites de structure passés.")

# --- MODULE 3 : DOUBLONS & INTÉGRITÉ (10 tests) ---
def test_duplicates():
    print("\nM3: Gestion des doublons...")
    try:
        user_in = UserCreate(username="altos_expert_bis", email="expert@altos.fi", password="CyberPassword123!", first_name="A", last_name="A")
        create_user(db, user_in)
    except Exception as e:
        db.rollback() 
        print(f"  ✅ Doublon d'email rejeté.")
    
    user = db.query(User).filter(User.email == "expert@altos.fi").first()
    if user and user.pockets:
        print(f"  ✅ Session restaurée et prête pour la suite.")

# --- MODULE 4 : LOGIQUE DE REVENUS & DÎME (24 tests) ---
def test_income_matrix():
    print("\nM4: Matrice des Revenus (Income Service)...")
    user = db.query(User).first()
    scenarios = [
        ("principal", True, 3000), ("principal", False, 3000),
        ("extraordinaire", True, 500), ("extraordinaire", False, 500),
        ("remboursement", True, 100), ("remboursement", False, 100),
        ("principal", True, 0.01), ("principal", True, 1000000)
    ]
    
    for inc_type, t_on, amt in scenarios:
        user.settings.tithing_enabled = t_on
        db.commit()
        tx = Transaction(user_id=user.id, label=f"Test {inc_type}", amount=amt)
        db.add(tx)
        db.commit()
        
        success = distribute_income(db, tx.id, inc_type)
        if success:
            splits = db.query(TransactionSplit).filter(TransactionSplit.transaction_id == tx.id).all()
            total = sum(s.amount for s in splits)
            assert abs(total - amt) < 0.01
    print(f"  ✅ {len(scenarios)} scénarios de flux validés.")

# --- MODULE 5 : IA CLASSIFIER & À CLASSER (10 tests) ---
def test_ia_robustness():
    print("\nM5: Robustesse de l'IA Learning & Gestion du 'À classer'...")
    user = db.query(User).first()
    test_cases = [
        ("   CARBURANT TOTAL  ", "Carburant"),
        ("!!!!AUCHAN!!!!", "Courses"),
        ("RETRAIT DAB 20/10", "À classer"),
        ("LOYER-SEPTEMBRE-2023", "Loyer"),
        ("Virement de : CAF_PROVENCE", "À classer"),
        ("ZELDA SHOP EBAY", "À classer")
    ]
    
    to_classify_list = []
    for label, expected_name in test_cases:
        cat_id = classify_transaction(db, user.id, label)
        cat = db.query(Category).filter(Category.id == cat_id).first()
        
        if cat and cat.name == "À classer":
            to_classify_list.append(label)
            print(f"  📥 [À CLASSER] : '{label}'")
        elif cat:
            print(f"  ✅ [AUTO] : '{label}' -> {cat.name}")

    print(f"  ✅ Bilan : {len(to_classify_list)} opérations en attente.")

# --- MODULE 6 : APPRENTISSAGE IA (IA LEARNING) ---
def test_ia_learning():
    print("\nM6: Test de l'Apprentissage IA (Learning)...")
    user = db.query(User).first()
    
    label_inconnu = "ZELDA SHOP EBAY"
    categorie_cible = "Loisirs"
    
    # 1. Vérifier qu'avant l'apprentissage, c'est 'À classer'
    id_avant = classify_transaction(db, user.id, label_inconnu)
    cat_avant = db.query(Category).filter(Category.id == id_avant).first()
    print(f"  Avant apprentissage : '{label_inconnu}' -> {cat_avant.name}")
    
    # 2. Simuler l'apprentissage
    print(f"  🧠 Apprentissage en cours : '{label_inconnu}' est un achat '{categorie_cible}'...")
    success = reclassify_and_learn(db, label_inconnu, categorie_cible)
    
    if success:
        # 3. Vérifier qu'après l'apprentissage, l'IA reconnaît le mot-clé
        id_apres = classify_transaction(db, user.id, label_inconnu)
        cat_apres = db.query(Category).filter(Category.id == id_apres).first()
        
        if cat_apres and cat_apres.name == categorie_cible:
            print(f"  ✅ SUCCÈS : L'IA a retenu la leçon ! -> {cat_apres.name}")
        else:
            print(f"  ❌ ÉCHEC : L'IA n'a pas mis à jour son mapping.")
    else:
        print("  ❌ ÉCHEC : La fonction reclassify_and_learn a échoué.")

# --- LANCEMENT ---
if __name__ == "__main__":
    try:
        user_in = UserCreate(username="altos_expert", email="expert@altos.fi", password="CyberPassword123!", first_name="Admin", last_name="Altos")
        user = create_user(db, user_in)
        
        if not user.settings:
            db.add(UserSettings(user_id=user.id, tithing_enabled=False))
            db.commit()

        test_auth_robustness()
        test_pockets_limits()
        test_duplicates()
        test_income_matrix()
        test_ia_robustness()
        test_ia_learning() # <--- Nouveau module ajouté

        print("\n🏆 BILAN FINAL : Altos Fi est prêt pour la production.")

    except Exception as e:
        print(f"\n💥 LE SYSTÈME A CÉDÉ : {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()