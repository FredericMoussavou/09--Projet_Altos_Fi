from app.core.database import SessionLocal, engine, Base
from app.crud.user import create_user
from app.schemas.user import UserCreate
from app.models.user import User, Pocket, Category

# On s'assure que les tables existent
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # 1. Création de l'utilisateur avec la structure par défaut (via JSON)
    user_in = UserCreate(
        username="test_custom",
        email="custom@altos.fi",
        password="Password123!",
        first_name="Test",
        last_name="Custom"
    )
    user = create_user(db, user_in)
    print(f"✅ Utilisateur créé avec succès.")

    # 2. AJOUT D'UNE NOUVELLE POCKET ("Vacances")
    # On vérifie d'abord combien il y a de pockets utilisateur (max 5)
    user_pockets_count = db.query(Pocket).filter(
        Pocket.user_id == user.id, 
        Pocket.is_system == False
    ).count()

    if user_pockets_count < 5:
        new_pocket = Pocket(
            user_id=user.id,
            name="Vacances",
            is_system=False
        )
        db.add(new_pocket)
        db.commit()
        print(f"✅ Nouvelle Pocket 'Vacances' créée (Total user pockets: {user_pockets_count + 1}/5).")
    else:
        print("❌ Limite de 5 pockets atteinte.")

    # 3. AJOUT D'UNE NOUVELLE CATÉGORIE DANS "BESOINS"
    # On récupère la pocket Besoins de cet utilisateur
    besoins_pocket = db.query(Pocket).filter(
        Pocket.user_id == user.id, 
        Pocket.name == "Besoins"
    ).first()

    if besoins_pocket:
        new_cat = Category(
            pocket_id=besoins_pocket.id,
            name="Crédit auto spécifique" # Nom différent pour bien le voir
        )
        db.add(new_cat)
        db.commit()
        print(f"✅ Catégorie 'Crédit auto spécifique' ajoutée à la Pocket 'Besoins'.")

    # 4. VÉRIFICATION FINALE
    print("\n--- État final de la structure ---")
    pockets = db.query(Pocket).filter(Pocket.user_id == user.id).all()
    for p in pockets:
        cats = db.query(Category).filter(Category.pocket_id == p.id).all()
        cat_names = [c.name for c in cats]
        print(f"Pocket: {p.name} | Catégories: {cat_names}")

finally:
    db.close()