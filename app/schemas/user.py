# app/schemas/user.py
import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

class GenderEnum(str, Enum):
    HOMME = "Homme"
    FEMME = "Femme"

# Schema de base : ce qui est commun à la création et à la lecture
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_dime_enabled: bool = False
    gender: Optional[GenderEnum] = None

# Schema pour la création (ce que le frontend envoie)
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator('password')
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not re.search(r'[A-Z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule.')
        if not re.search(r'[a-z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une minuscule.')
        if not re.search(r'[0-9]', v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>+]', v):
            raise ValueError('Le mot de passe doit contenir au moins un caractère spécial.')
        return v

# Schema pour la lecture (ce que l'API renvoie au frontend)
class UserOut(UserBase):
    id: UUID
    is_premium: bool
    created_at: datetime

    class Config:
        # Cette ligne permet à Pydantic de lire les données 
        # même si ce sont des objets de base de données (SQLAlchemy)
        from_attributes = True