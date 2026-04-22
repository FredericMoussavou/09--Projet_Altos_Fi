from app.core.database import SessionLocal
from app.crud.user import create_user, create_pocket
from app.schemas.user import UserCreate

db = SessionLocal()
user_in = UserCreate(username="test_limit", email="limit@altos.fi", password="Password123!", first_name="L", last_name="T")

try:
    user = create_user(db, user_in)
    print("✅ Utilisateur créé (avec ses 4 pockets par défaut).")

    print("→ Tentative d'ajout de la 5ème pocket (Vacances)...")
    create_pocket(db, user.id, "Vacances")
    print("✅ 5ème pocket acceptée.")

    print("→ Tentative d'ajout de la 6ème pocket (Mariage)...")
    create_pocket(db, user.id, "Mariage")
    print("✅ 6ème pocket acceptée (Oups, il y a un problème !)")

except Exception as e:
    print(f"❌ Blocage réussi : {e}")

finally:
    db.close()