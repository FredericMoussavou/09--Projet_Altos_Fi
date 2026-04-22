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
    @staticmethod
    def update_budget_line(db: Session, budget_id: str, new_amount: float):
        """
        Analyse la modification de Paul et définit l'action à entreprendre.
        """
        budget = db.query(Budget).filter(Budget.id == budget_id).first()
        old_amount = budget.estimated_amount

        # Cas 1 : Paul met à 0
        if new_amount == 0:
            return {
                "status": "NEED_CONFIRMATION",
                "question": "FINISHED_OR_POSTPONED",
                "message": "Cette dépense est-elle terminée ou simplement reportée ?"
            }

        # Cas 2 : Augmentation
        elif new_amount > old_amount:
            return {
                "status": "NEED_CONFIRMATION",
                "question": "ANTICIPATION_OR_NEW_BASE",
                "message": "Est-ce une anticipation (remboursement accéléré) ou un nouveau montant permanent ?"
            }

        # Cas 3 : Diminution
        elif new_amount < old_amount:
            return {
                "status": "NEED_CONFIRMATION",
                "question": "TEMP_ADJUST_OR_NEW_BASE",
                "message": "Est-ce une baisse ponctuelle ou un nouveau montant permanent ?"
            }

        return {"status": "SUCCESS", "action": "IMMEDIATE_UPDATE"}
    
    @staticmethod
    def confirm_budget_veto(db: Session, budget_id: str, new_amount: float, decision: str):
        """
        Applique la décision de Paul suite à un changement de montant.
        Décisions possibles : 'TERMINATED', 'POSTPONED', 'ANTICIPATION', 'NEW_BASE', 'TEMP'
        """
        budget = db.query(Budget).filter(Budget.id == budget_id).first()
        category = budget.category

        if decision == "TERMINATED":
            # Le montant ne se présente plus les mois d'après
            budget.estimated_amount = 0
            # Optionnel : on pourrait désactiver la catégorie ou la dette associée
            debt = db.query(Debt).filter(Debt.category_id == category.id).first()
            if debt:
                debt.status = "completed"

        elif decision == "NEW_BASE":
            # On met à jour le montant actuel ET on en fait la nouvelle référence
            budget.estimated_amount = new_amount
            # L'IA utilisera ce montant comme M-1 le mois prochain

        elif decision == "POSTPONED" or decision == "TEMP":
            # On change juste ce mois-ci
            budget.estimated_amount = new_amount
            # Le mois prochain, le moteur reprendra l'historique M-1 ou la Dette

        elif decision == "ANTICIPATION":
            # Paul paie plus pour solder. On met à jour le montant.
            budget.estimated_amount = new_amount
            # On pourrait ici ajouter une logique pour réduire le capital de la dette

        db.commit()
        return {"status": "SUCCESS", "new_amount": budget.estimated_amount}