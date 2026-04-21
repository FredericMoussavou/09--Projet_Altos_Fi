from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from uuid import UUID
from app.services.budget_engine import allocate_income
from app.core.database import get_db
from app.schemas.transaction import TransactionCreate, TransactionOut
from app.crud import transaction as crud_transaction
from app.api.auth import get_current_user
from app.models.user import User, Transaction

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/", response_model=TransactionOut)
def add_transaction(
    transaction_in: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enregistre une nouvelle transaction pour l'utilisateur connecté.
    C'est ici que les revenus bancaires arriveront.
    """
    return crud_transaction.create_transaction(
        db=db, 
        transaction_in=transaction_in, 
        user_id=current_user.id
    )

@router.get("/unprocessed", response_model=List[TransactionOut])
def read_unprocessed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste les transactions qui n'ont pas encore été allouées au budget."""
    return crud_transaction.get_unprocessed_transactions(db, user_id=current_user.id)

@router.post("/{transaction_id}/allocate")
def process_allocation(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # CONVERSION CRUCIALE : On transforme la string en objet UUID pour SQLite
    try:
        uuid_obj = uuid.UUID(transaction_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Format d'ID invalide")

    # On utilise uuid_obj au lieu de transaction_id
    transaction = db.query(Transaction).filter(
        Transaction.id == uuid_obj, 
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction non trouvée")
    
    if transaction.is_processed:
        raise HTTPException(status_code=400, detail="Transaction déjà traitée")
        
    allocation_result = allocate_income(db, current_user, transaction)
    return {
        "message": "Répartition effectuée avec succès",
        "allocation": allocation_result
    }