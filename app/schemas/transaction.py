from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.models.user import TransactionSource

class TransactionBase(BaseModel):
    label: str
    amount: float
    source: TransactionSource = TransactionSource.AUTRE

class TransactionCreate(TransactionBase):
    pass

class TransactionOut(TransactionBase):
    id: UUID
    date: datetime
    is_processed: bool

    # Nouvelle syntaxe Pydantic V2
    model_config = ConfigDict(from_attributes=True)