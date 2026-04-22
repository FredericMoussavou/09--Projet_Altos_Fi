from app.core.database import SessionLocal, Base, engine
from app.crud.user import create_user
from app.schemas.user import UserCreate
from app.models.user import Transaction, Category
from app.services.classifier import classify_transaction

db = SessionLocal()
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

try:
    # 1. Création user
    user_in = UserCreate(username="gege", email="gege@test.com", password="Password123!", first_name="G", last_name="E")
    user = create_user(db, user_in)

    # 2. Liste de transactions brutes (simulant un CSV)
    raw_transactions = [
        {"label": "CB SUPER U 85000", "amount": 65.40},
        {"label": "PREL EDF JANVIER", "amount": 89.00},
        {"label": "PATISSERIE MOUILLERON", "amount": 12.50} # Inconnu dans ton JSON
    ]

    print("📥 Importation des transactions...")
    for raw in raw_transactions:
        cat_id = classify_transaction(db, user.id, raw["label"])
        
        tx = Transaction(
            user_id=user.id,
            label=raw["label"],
            amount=raw["amount"],
            category_id=cat_id
        )
        db.add(tx)
        
        status = "Classé" if cat_id else "À CLASSER"
        print(f"  - {raw['label']} ({raw['amount']}€) -> {status}")

    db.commit()

finally:
    db.close()