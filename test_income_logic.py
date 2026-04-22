from app.core.database import SessionLocal, engine, Base
from app.crud.user import create_user
from app.schemas.user import UserCreate
from app.models.user import User, UserSettings, Transaction, TransactionSplit, Pocket, Category
from app.services.income_service import distribute_income
import json

# Initialisation base de test
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
db = SessionLocal()

def run_test():
    print("🧪 DÉMARRAGE DU TEST DE VENTILATION DES REVENUS\n")
    
    # 1. Création de l'utilisateur
    user_in = UserCreate(username="paul_altos", email="paul@altos.fi", password="Password123!", first_name="Paul", last_name="Altos")
    user = create_user(db, user_in)
    
    # S'assurer que UserSettings existe (si ton crud ne le crée pas auto)
    if not user.settings:
        user_settings = UserSettings(user_id=user.id, tithing_enabled=False)
        db.add(user_settings)
        db.commit()
        db.refresh(user)

    def test_scenario(label, amount, inc_type, tithing_on):
        print(f"--- {label} ---")
        # Mise à jour du toggle
        user.settings.tithing_enabled = tithing_on
        db.commit()

        # Création de la transaction brute
        tx = Transaction(user_id=user.id, label=label, amount=amount)
        db.add(tx)
        db.commit()

        # Exécution de la ventilation
        distribute_income(db, tx.id, inc_type)
        
        # Vérification des Splits
        splits = db.query(TransactionSplit).filter(TransactionSplit.transaction_id == tx.id).all()
        
        dime_split = next((s for s in splits if "Dîme" in (s.label or "")), None)
        total_distribue = sum(s.amount for s in splits)
        
        print(f"   Toggle Dîme: {'ON' if tithing_on else 'OFF'}")
        print(f"   Dîme prélevée: {dime_split.amount if dime_split else 0}€")
        print(f"   Nombre de poches alimentées: {len(splits) - (1 if dime_split else 0)}")
        print(f"   Total réparti (Dîme incluse): {total_distribue}€")
        
        if abs(total_distribue - amount) < 0.01:
            print("   ✅ RÈGLE : La somme est exacte.")
        else:
            print(f"   ❌ ERREUR : Somme incorrecte ({total_distribue} vs {amount})")
        print("-" * 40)

    # Lancement des Scénarios
    # 1 & 2 : Salaire (Automatique)
    test_scenario("SALAIRE PAUL", 3000.0, "principal", tithing_on=False)
    test_scenario("SALAIRE PAUL", 3000.0, "principal", tithing_on=True)

    # 3 & 4 : Extraordinaire (Manuel)
    test_scenario("DON TANTE GERTRUDE", 70.0, "extraordinaire", tithing_on=False)
    test_scenario("DON TANTE GERTRUDE", 70.0, "extraordinaire", tithing_on=True)

    # 5 & 6 : Remboursement (Jamais de Dîme)
    test_scenario("PRET FRERE", 100.0, "remboursement", tithing_on=False)
    test_scenario("PRET FRERE", 100.0, "remboursement", tithing_on=True)

run_test()
db.close()