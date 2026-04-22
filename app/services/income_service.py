import json
import os
from sqlalchemy.orm import Session
from app.models.user import Transaction, TransactionSplit, Pocket, Category, UserSettings

SETTINGS_PATH = os.path.join("app", "core", "settings.json")

def distribute_income(db: Session, transaction_id: str, income_type: str, manual_splits: list = None):
    """
    Service de ventilation Altos Fi.
    Types : 'principal' (Auto), 'extraordinaire' (Dîme + Manuel), 'remboursement' (Manuel)
    """
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx or tx.amount <= 0:
        return False

    user = tx.user
    # On récupère les réglages via la relation (ou création si absent par sécurité)
    settings_user = user.settings
    tithing_active = settings_user.tithing_enabled if settings_user else False

    # Chargement des constantes globales
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        global_settings = json.load(f)
    
    tithing_ratio = global_settings.get("tithing", {}).get("default_ratio", 0.1)
    remaining_amount = tx.amount

    # --- ÉTAPE 1 : GESTION DE LA DÎME ---
    if tithing_active and income_type in ['principal', 'extraordinaire']:
        tithing_amount = tx.amount * tithing_ratio
        
        tithing_cat = db.query(Category).join(Pocket).filter(
            Pocket.user_id == user.id, 
            Category.name == "Dîme"
        ).first()
        
        if tithing_cat:
            split_dime = TransactionSplit(
                transaction_id=tx.id,
                pocket_id=tithing_cat.pocket_id,
                category_id=tithing_cat.id,
                amount=tithing_amount,
                label="Prélèvement Dîme"
            )
            db.add(split_dime)
            remaining_amount -= tithing_amount

    # --- ÉTAPE 2 : RÉPARTITION DU SOLDE ---
    
    # CAS A : REVENU PRINCIPAL (Ventilation Automatique)
    if income_type == 'principal':
        ratios = global_settings["income_distribution"]["default_ratios"]
        
        # TODO : Ici, on pourrait aller chercher des UserDistributionPreference 
        # si l'utilisateur a personnalisé ses ratios.
        
        for pocket_name, ratio in ratios.items():
            pocket = db.query(Pocket).filter(Pocket.name == pocket_name, Pocket.user_id == user.id).first()
            if pocket:
                # On affecte à la catégorie par défaut de la pocket
                cat = db.query(Category).filter(Category.pocket_id == pocket.id).first()
                split_amount = remaining_amount * ratio
                
                db.add(TransactionSplit(
                    transaction_id=tx.id,
                    pocket_id=pocket.id,
                    category_id=cat.id if cat else None,
                    amount=split_amount,
                    label=f"Auto-Ventilation {pocket_name}"
                ))

    # CAS B : EXTRAORDINAIRE OU REMBOURSEMENT (Ventilation Manuelle)
    elif income_type in ['extraordinaire', 'remboursement']:
        if manual_splits:
            # L'utilisateur a déjà envoyé sa décision
            for item in manual_splits:
                pocket = db.query(Pocket).filter(Pocket.name == item['pocket_name'], Pocket.user_id == user.id).first()
                if pocket:
                    db.add(TransactionSplit(
                        transaction_id=tx.id,
                        pocket_id=pocket.id,
                        amount=item['amount'],
                        label=f"Ventilation manuelle ({income_type})"
                    ))
        else:
            # On laisse le solde dans "À classer" ou on marque la transaction
            # pour une action utilisateur dans l'interface.
            cat_a_classer = db.query(Category).filter(Category.name == "À classer").first()
            db.add(TransactionSplit(
                transaction_id=tx.id,
                pocket_id=cat_a_classer.pocket_id if cat_a_classer else None,
                category_id=cat_a_classer.id if cat_a_classer else None,
                amount=remaining_amount,
                label="Attente de ventilation manuelle"
            ))

    db.commit()
    return True