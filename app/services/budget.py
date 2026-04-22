import json
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import Transaction, BudgetLine, Category, Pocket
from datetime import datetime, timedelta

def generate_monthly_budget(db: Session, user_id: str, month: int, year: int):
    # 1. Charger les règles de l'IA
    with open("app/core/ai_rules.json") as f:
        rules = json.load(f)
    
    # 2. Récupérer toutes les catégories de l'utilisateur
    categories = db.query(Category).join(Pocket).filter(Pocket.user_id == user_id).all()
    
    budget_lines = []

    for category in categories:
        # 3. Récupérer les montants des 3 derniers mois pour cette catégorie
        # On simule ici la logique : on cherche le max mensuel sur les 90 derniers jours
        three_months_ago = datetime.now() - timedelta(days=90)
        
        # Somme des transactions par mois pour cette catégorie
        # (Pour le test simplifié, on prend le max de toutes les transactions isolées)
        max_amount = db.query(func.max(Transaction.amount)).filter(
            Transaction.category_id == category.id,
            Transaction.date >= three_months_ago
        ).scalar() or 0.0

        # 4. Créer la ligne de budget (Le Théorique)
        db_line = BudgetLine(
            category_id=category.id,
            month=month,
            year=year,
            planned_amount=max_amount,
            actual_amount=0.0 # Sera rempli au fur et à mesure du mois
        )
        db.add(db_line)
        budget_lines.append(db_line)
    
    db.commit()
    return budget_lines