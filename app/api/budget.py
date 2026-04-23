from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.services.budget_service import BudgetService

router = APIRouter(prefix="/budget", tags=["budget"])

@router.post("/generate/{month}/{year}")
def generate_monthly_budget(
    month: int, 
    year: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Génère le budget initial de Paul pour un mois donné."""
    has_alert = BudgetService.generate_initial_budget(db, current_user.id, month, year)
    return {"has_alert": has_alert, "message": "Budget généré avec succès"}

@router.patch("/line/{budget_id}")
def update_budget_line(
    budget_id: str, 
    new_amount: float, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Action de Paul : modifier un montant. Retourne potentiellement une question."""
    # Note : On devrait vérifier que le budget appartient bien au current_user ici
    return BudgetService.update_budget_line(db, budget_id, new_amount)

@router.post("/confirm-veto")
def confirm_veto(
    budget_id: str, 
    new_amount: float, 
    decision: str, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Paul répond à la question (ex: 'NEW_BASE', 'TERMINATED')."""
    return BudgetService.confirm_budget_veto(db, budget_id, new_amount, decision)