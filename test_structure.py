from app.core.database import SessionLocal, engine, Base
from app.crud.user import create_user
from app.schemas.user import UserCreate
from app.models.user import User, Pocket, Category

# Création des tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Données de test
user_in = UserCreate(
    username="test_philosophie2",
    email="test2@altos.fi",
    password="Password123!",
    first_name="Jean2",
    last_name="Test2"
)

try:
    user = create_user(db, user_in)
    print(f"✅ Utilisateur {user.username} créé.")
    
    pockets = db.query(Pocket).filter(Pocket.user_id == user.id).all()
    print(f"📊 Nombre de Pockets créées : {len(pockets)} (Attendu : 6 - Dîme, À classer, Besoins, Envies, Épargne, Dons)")
    
    for p in pockets:
        cats = db.query(Category).filter(Category.pocket_id == p.id).all()
        print(f"   - Pocket '{p.name}' (Système: {p.is_system}) : {len(cats)} catégories")

finally:
    db.close()