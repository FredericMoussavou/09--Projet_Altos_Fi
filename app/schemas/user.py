# app/schemas/user.py
import re
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

class GenderEnum(str, Enum):
    HOMME = "Homme"
    FEMME = "Femme"

#Validation mot de passe

def validate_password_complexity(v: str) -> str:
    """Fonction réutilisable pour valider la complexité du mot de passe."""
    if not re.search(r'[A-Z]', v):
        raise ValueError('Le mot de passe doit contenir au moins une majuscule.')
    if not re.search(r'[a-z]', v):
        raise ValueError('Le mot de passe doit contenir au moins une minuscule.')
    if not re.search(r'[0-9]', v):
        raise ValueError('Le mot de passe doit contenir au moins un chiffre.')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>+]', v):
        raise ValueError('Le mot de passe doit contenir au moins un caractère spécial.')
    return v


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
    def validate_password(cls, v: str) -> str:
        return validate_password_complexity(v)

# Schema pour la lecture (ce que l'API renvoie au frontend)
class UserOut(UserBase):
    id: UUID
    is_premium: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return validate_password_complexity(v)

class PasswordReset(BaseModel):
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_complexity(v)