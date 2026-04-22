from app.core.database import SessionLocal, Base, engine
from app.crud.user import create_user
from app.schemas.user import UserCreate
from app.models.user import Transaction, Category, Pocket
from app.services.budget import generate_monthly_budget
from datetime import datetime

db = SessionLocal()
# Nettoyage pour le test
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

try:
    # 1. Création utilisateur
    user_in = UserCreate(username="test_ai", email="ai@altos.fi", password="Password123!", first_name="IA", last_name="Test")
    user = create_user(db, user_in)
    
    # 2. On récupère la catégorie "Courses" pour lui injecter des données
    courses_cat = db.query(Category).filter(Category.name == "Courses").first()

    # 3. SIMULATION DE 3 MOIS (Principe de Prudence)
    # Mai : 450€ | Juin : 520€ | Juillet : 480€
    montants = [450.0, 520.0, 480.0]
    for m in montants:
        tx = Transaction(user_id=user.id, category_id=courses_cat.id, amount=m, label="Courses supermarché")
        db.add(tx)
    db.commit()

    print(f"📊 Historique injecté pour 'Courses' : {montants}")

    # 4. LANCEMENT DU CERVEAU POUR AOÛT
    print("🤖 L'IA calcule le budget d'Août...")
    generate_monthly_budget(db, user.id, 8, 2025)

    # 5. VÉRIFICATION
    from app.models.user import BudgetLine
    result = db.query(BudgetLine).filter(BudgetLine.category_id == courses_cat.id).first()
    
    print(f"✅ Budget prévu pour Août : {result.planned_amount}€")
    
    if result.planned_amount == 520.0:
        print("🏆 SUCCÈS : L'IA a bien choisi le montant maximum (Prudence).")
    else:
        print(f"❌ ÉCHEC : L'IA a choisi {result.planned_amount} au lieu de 520.0")

finally:
    db.close()