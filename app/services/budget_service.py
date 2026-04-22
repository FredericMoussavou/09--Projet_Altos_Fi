from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.user import Category, CategoryType, Budget, Debt, Transaction
from datetime import datetime, timedelta

class BudgetService:
    @staticmethod
    def get_average_income(db: Session, user_id: str, months: int = 3):
        """
        Calcule dynamiquement le revenu moyen basé sur les transactions positives 
        classées dans des catégories de type 'Revenu' ou sans catégorie (selon ta logique).
        """
        three_months_ago = datetime.now() - timedelta(days=months * 30)
        
        # On somme les transactions positives (entrées d'argent) sur les 3 derniers mois
        total_income = db.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.amount > 0,
                Transaction.date >= three_months_ago
            )
        ).scalar() or 0.0
        
        return total_income / months

    @staticmethod
    def get_historical_average(db: Session, category_id: str, months: int = 3):
        """Calcule la moyenne réelle des dépenses pour une catégorie spécifique."""
        three_months_ago = datetime.now() - timedelta(days=months * 30)
        
        # On prend la valeur absolue car les dépenses sont souvent négatives en base
        avg = db.query(func.avg(func.abs(Transaction.amount))).filter(
            and_(
                Transaction.category_id == category_id,
                Transaction.date >= three_months_ago
            )
        ).scalar() or 0.0
        
        return float(avg)

    @staticmethod
    def generate_initial_budget(db: Session, user_id: str, month: int, year: int, mode="prorata"):
        """
        Génère le budget en confrontant REVENUS RÉELS vs DÉPENSES RÉELLES.
        """
        income = BudgetService.get_average_income(db, user_id)
        categories = db.query(Category).join(Category.pocket).filter(Category.pocket.has(user_id=user_id)).all()
        
        estimates = {}
        fixed_total = 0.0
        variable_total_hist = 0.0

        for cat in categories:
            # 1. Détermination du montant de base (Dette > Historique > 0)
            debt = db.query(Debt).filter(Debt.category_id == cat.id, Debt.status == "active").first()
            
            if debt:
                val = debt.monthly_installment
            else:
                val = BudgetService.get_historical_average(db, cat.id)
            
            estimates[cat.id] = val
            
            # 2. Cumul pour arbitrage
            if cat.type == CategoryType.FIXED:
                fixed_total += val
            else:
                variable_total_hist += val

        grand_total = fixed_total + variable_total_hist

        # 3. Logique d'ajustement automatique si dépassement des revenus
        if grand_total > income and income > 0:
            available_for_vars = max(0, income - fixed_total)
            
            if mode == "prorata" and variable_total_hist > 0:
                for cat in [c for c in categories if c.type == CategoryType.VARIABLE]:
                    ratio = estimates[cat.id] / variable_total_hist
                    estimates[cat.id] = ratio * available_for_vars

        # 4. Persistence en base de données
        created_budgets = []
        for cat_id, amount in estimates.items():
            new_budget = Budget(
                category_id=cat_id,
                month=month,
                year=year,
                estimated_amount=round(amount, 2)
            )
            db.add(new_budget)
            created_budgets.append(new_budget)
        
        db.commit()
        return grand_total > income # True si alerte nécessaire