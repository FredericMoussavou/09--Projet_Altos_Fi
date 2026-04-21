from sqlalchemy.orm import Session
from app.models.user import Transaction
from app.schemas.transaction import TransactionCreate
from uuid import UUID

def create_transaction(db: Session, transaction_in: TransactionCreate, user_id: UUID):
    db_obj = Transaction(
        **transaction_in.model_dump(),
        user_id=user_id,
        is_processed=False
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_unprocessed_transactions(db: Session, user_id: UUID):
    return db.query(Transaction).filter(
        Transaction.user_id == user_id, 
        Transaction.is_processed == False
    ).all()