from app.core.database import SessionLocal
from app.models.user import Transaction, Category
from app.services.classifier import reclassify_and_learn, classify_transaction
import json

db = SessionLocal()

try:
    # 1. On récupère la transaction "Pâtisserie" (créée lors du test précédent)
    tx = db.query(Transaction).filter(Transaction.label.contains("PATISSERIE")).first()
    
    # 2. On récupère l'ID de la catégorie "Restauration"
    restau_cat = db.query(Category).filter(Category.name == "Restauration").first()

    print(f"🔄 Reclassification de '{tx.label}' vers 'Restauration'...")
    
    # 3. Action de l'utilisateur : "Dorénavant, PATISSERIE = Restauration"
    success = reclassify_and_learn(db, tx.id, restau_cat.id, "PATISSERIE")

    if success:
        print("✅ Transaction mise à jour et mot-clé ajouté au dictionnaire.")
        
        # 4. VÉRIFICATION : Est-ce que l'IA reconnaît une NOUVELLE pâtisserie maintenant ?
        print("🤖 Test de l'IA sur une nouvelle transaction : 'BOULANGERIE PATISSERIE DU CENTRE'")
        new_cat_id = classify_transaction(db, tx.user_id, "BOULANGERIE PATISSERIE DU CENTRE")
        
        if new_cat_id == restau_cat.id:
            print("🏆 VICTOIRE : L'IA a appris ! Elle classe automatiquement la nouvelle pâtisserie.")
        else:
            print("❌ L'IA n'a pas reconnu le mot-clé.")

finally:
    db.close()