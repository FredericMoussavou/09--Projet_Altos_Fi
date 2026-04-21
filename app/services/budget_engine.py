from sqlalchemy.orm import Session
from app.models.user import User, Transaction
from typing import Dict

def allocate_income(db: Session, user: User, transaction: Transaction) -> Dict:
    """
    Moteur de calcul : Prend un revenu brut et le ventile selon les 
    préférences de l'utilisateur (Option B).
    """
    amount = transaction.amount
    prefs = user.preferences
    
    # 1. Calcul de la Dîme (si activée)
    tithing_amount = 0.0
    if prefs.tithing_enabled:
        tithing_amount = amount * (prefs.tithing_percentage / 100)
    
    # 2. Montant restant à répartir
    remainder = amount - tithing_amount
    
    # 3. Répartition selon les ratios (Besoins, Envies, Épargne, Dons supp.)
    allocation = {
        "tithe": round(tithing_amount, 2),
        "needs": round(remainder * (prefs.ratio_needs / 100), 2),
        "wants": round(remainder * (prefs.ratio_wants / 100), 2),
        "savings": round(remainder * (prefs.ratio_savings / 100), 2),
        "extra_give": round(remainder * (prefs.ratio_give / 100), 2)
    }
    
    # 4. Marquage de la transaction comme traitée
    transaction.is_processed = True
    db.commit()
    
    return allocation