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

class GenderEnum(str, enum.Enum):
    HOMME = "Homme"
    FEMME = "Femme"

class TransactionSource(str, enum.Enum):
    SALAIRE = "Salaire"
    BUSINESS = "Business"
    CADEAU = "Cadeau"
    AUTRE = "Autre"

# --- TABLES PRINCIPALES ---

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    gender = Column(Enum(GenderEnum), nullable=True)
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    pockets = relationship("Pocket", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    birth_date = Column(Date, nullable=True)
    main_income = Column(Float, default=0.0)
    marital_status = Column(Enum(MaritalStatus), default=MaritalStatus.CELIBATAIRE)
    user = relationship("User", back_populates="profile")

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    # Ratios pour les 5 Pockets (hors Dîme)
    ratio_needs = Column(Integer, default=50)
    ratio_wants = Column(Integer, default=30)
    ratio_savings = Column(Integer, default=10)
    ratio_donations = Column(Integer, default=10)
    ratio_extra = Column(Integer, default=0) # Pour la 5ème pocket personnalisée
    # Dîme (La Super Pocket)
    tithing_enabled = Column(Boolean, default=True)
    tithing_percentage = Column(Float, default=10.0)
    user = relationship("User", back_populates="preferences")

# --- STRUCTURE BUDGÉTAIRE (Inspirée de tes Excel) ---

class Pocket(Base):
    """Enveloppes : Besoins, Envies, Épargne, Dons, Perso + À Classer"""
    __tablename__ = "pockets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False) 
    is_system = Column(Boolean, default=False) # True pour "À classer" et "Dîme"
    
    user = relationship("User", back_populates="pockets")
    categories = relationship("Category", back_populates="pocket", cascade="all, delete-orphan")

class Category(Base):
    """Postes de dépenses (Loyer, EDF, Restaurant...)"""
    __tablename__ = "categories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pocket_id = Column(UUID(as_uuid=True), ForeignKey("pockets.id"), nullable=False)
    name = Column(String, nullable=False)
    
    pocket = relationship("Pocket", back_populates="categories")
    budget_lines = relationship("BudgetLine", back_populates="category", cascade="all, delete-orphan")

class BudgetLine(Base):
    """Le Prévisionnel vs Réalisé mensuel"""
    __tablename__ = "budget_lines"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    planned_amount = Column(Float, default=0.0) # Basé sur le "Principe de Prudence"
    actual_amount = Column(Float, default=0.0)  # Somme des transactions réelles
    
    category = relationship("Category", back_populates="budget_lines")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True) # None = À classer
    label = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(Enum(TransactionSource), default=TransactionSource.AUTRE)
    is_processed = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="transactions")

class UserDistributionPreference(Base):
    """Stocke les % de répartition choisis par l'utilisateur pour ses pockets."""
    __tablename__ = "user_distribution_preferences"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    pocket_id = Column(String, ForeignKey("pockets.id"))
    percentage = Column(Float, nullable=False) # Ex: 0.50 pour 50%

class TransactionSplit(Base):
    """Permet de diviser une transaction entrante (Revenu) sur plusieurs destinations."""
    __tablename__ = "transaction_splits"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String, ForeignKey("transactions.id"))
    pocket_id = Column(String, ForeignKey("pockets.id"))
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    amount = Column(Float, nullable=False)
    label = Column(String, nullable=True) # Ex: "Part Besoins du salaire"