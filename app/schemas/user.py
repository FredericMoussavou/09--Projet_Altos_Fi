from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict
from typing import Optional
from datetime import date, datetime
from uuid import UUID
import re
from enum import Enum

# --- ENUMS ---

class GenderEnum(str, Enum):
    HOMME = "Homme"
    FEMME = "Femme"

class MaritalStatus(str, Enum):
    CELIBATAIRE = "Célibataire"
    MARIE = "Marié"
    PACS = "Pacsé"
    CONCUBINAGE = "En couple"
    DIVORCE = "Divorcé"
    VEUF = "Veuf"

# --- VALIDATEURS ---

def validate_password_complexity(v: str) -> str:
    if not re.search(r'[A-Z]', v):
        raise ValueError('Le mot de passe doit contenir au moins une majuscule.')
    if not re.search(r'[a-z]', v):
        raise ValueError('Le mot de passe doit contenir au moins une minuscule.')
    if not re.search(r'[0-9]', v):
        raise ValueError('Le mot de passe doit contenir au moins un chiffre.')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>+]', v):
        raise ValueError('Le mot de passe doit contenir au moins un caractère spécial.')
    return v

# --- SCHEMAS AUTH ---

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

# --- SCHEMAS USER ---

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[GenderEnum] = None
    tithing_enabled: bool = False

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    @field_validator('password')
    @classmethod
    def validate_pw(cls, v: str) -> str:
        return validate_password_complexity(v)

class UserOut(UserBase):
    id: UUID
    is_premium: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- SCHEMAS PREFERENCES (La règle des 100%) ---

class UserPreferencesBase(BaseModel):
    ratio_needs: int = 50
    ratio_wants: int = 30
    ratio_savings: int = 20
    ratio_give: int = 0
    tithing_enabled: bool = True
    tithing_percentage: float = 10.0
    morning_briefing_enabled: bool = True
    instant_alerts_enabled: bool = True
    global_alert_threshold: float = 0.15
    lock_vases_communicants: bool = True
    class Config:
        from_attributes = True

    @model_validator(mode='after')
    def validate_ratios_sum(self) -> 'UserPreferencesBase':
        total = self.ratio_needs + self.ratio_wants + self.ratio_savings + self.ratio_give
        if total != 100:
            raise ValueError(f"La somme des ratios doit être égale à 100. Total actuel : {total}")
        return self

# --- SCHEMAS PROFILE ---

class ProfileBase(BaseModel):
    birth_date: Optional[date] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    main_income: float = 0.0
    marital_status: MaritalStatus = MaritalStatus.CELIBATAIRE

class ProfileUpdate(ProfileBase):
    pass

class ProfileOut(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

# --- SCHEMAS DE PRÉFÉRENCES (Version Lecture) ---
class UserPreferencesOut(UserPreferencesBase):
    model_config = ConfigDict(from_attributes=True)

# --- SCHEMA GLOBAL AGRÉGÉ ---
class UserGlobalOut(UserOut):
    profile: Optional[ProfileOut] = None
    preferences: Optional[UserPreferencesOut] = None
    # On ajoutera "notifications: List[NotificationOut]" ici plus tard
    
    model_config = ConfigDict(from_attributes=True)