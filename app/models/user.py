import enum
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Date, Float, Enum, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

# --- ENUMS ---

class MaritalStatus(str, enum.Enum):
    CELIBATAIRE = "Célibataire"
    MARIE = "Marié"
    PACS = "Pacsé"
    CONCUBINAGE = "En couple"
    DIVORCE = "Divorcé"
    VEUF = "Veuf"

class BudgetType(str, enum.Enum):
    SOLO = "Solo"
    JOINT = "Joint"

class MemberRole(str, enum.Enum):
    OWNER = "Owner"
    MEMBER = "Member"

class GenderEnum(str, enum.Enum):
    HOMME = "Homme"
    FEMME = "Femme"

# --- TABLES ---

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    # Récupération des champs de ton ancien schéma
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    gender = Column(Enum(GenderEnum), nullable=True)
    
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    bank_accounts = relationship("BankAccount", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("BudgetMember", back_populates="user")

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    birth_date = Column(Date, nullable=True)
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=True)
    main_income = Column(Float, default=0.0)
    marital_status = Column(Enum(MaritalStatus), default=MaritalStatus.CELIBATAIRE)
    id_document_path = Column(String, nullable=True)
    avatar_path = Column(String, nullable=True)
    user = relationship("User", back_populates="profile")

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    ratio_needs = Column(Integer, default=50)
    ratio_wants = Column(Integer, default=30)
    ratio_savings = Column(Integer, default=20)
    ratio_give = Column(Integer, default=0)
    tithing_enabled = Column(Boolean, default=True)
    tithing_percentage = Column(Float, default=10.0)
    user = relationship("User", back_populates="preferences")

class BankAccount(Base):
    __tablename__ = "bank_accounts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    bank_name = Column(String, nullable=False)
    account_type = Column(String)
    current_balance = Column(Float, default=0.0)
    api_provider_id = Column(String, unique=True, nullable=True)
    last_sync = Column(DateTime(timezone=True), onupdate=func.now())
    user = relationship("User", back_populates="bank_accounts")

class Budget(Base):
    __tablename__ = "budgets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    type = Column(Enum(BudgetType), default=BudgetType.SOLO)
    is_locked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    members = relationship("BudgetMember", back_populates="budget")

class BudgetMember(Base):
    __tablename__ = "budget_members"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    budget_id = Column(UUID(as_uuid=True), ForeignKey("budgets.id"), primary_key=True)
    role = Column(Enum(MemberRole), default=MemberRole.OWNER)
    user = relationship("User", back_populates="budgets")
    budget = relationship("Budget", back_populates="members")