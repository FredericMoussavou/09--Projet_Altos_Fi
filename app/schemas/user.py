# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

# Schema de base : ce qui est commun à la création et à la lecture
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_dime_enabled: bool = False
    gender: Optional[str] = None

# Schema pour la création (ce que le frontend envoie)
class UserCreate(UserBase):
    password: str # Ici, c'est le mot de passe en clair envoyé par l'utilisateur

# Schema pour la lecture (ce que l'API renvoie au frontend)
class UserOut(UserBase):
    id: UUID
    is_premium: bool
    created_at: datetime

    class Config:
        # Cette ligne permet à Pydantic de lire les données 
        # même si ce sont des objets de base de données (SQLAlchemy)
        from_attributes = True