import enum
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Date, Float, Enum, Integer
from sqlalchemy.orm import relationship
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

# --- TABLES DE CONFIGURATION ---

class UserSettings(Base):
    """Centrale des préférences de l'utilisateur."""
    __tablename__ = "user_settings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), unique=True)
    
    # Toggle Dîme par défaut à False selon tes instructions
    tithing_enabled = Column(Boolean, default=False) 
    
    user = relationship("User", back_populates="settings")

class UserDistributionPreference(Base):
    """Stocke les % de répartition choisis par l'utilisateur pour ses pockets."""
    __tablename__ = "user_distribution_preferences"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    pocket_id = Column(String, ForeignKey("pockets.id"))
    percentage = Column(Float, nullable=False) # Ex: 0.50 pour 50%

# --- TABLES PRINCIPALES ---

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    birth_date = Column(Date)
    gender = Column(Enum(GenderEnum), nullable=True)
    marital_status = Column(Enum(MaritalStatus), default=MaritalStatus.CELIBATAIRE)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    pockets = relationship("Pocket", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

class Pocket(Base):
    __tablename__ = "pockets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="pockets")
    categories = relationship("Category", back_populates="pocket", cascade="all, delete-orphan")

class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pocket_id = Column(String, ForeignKey("pockets.id"), nullable=False)
    name = Column(String, nullable=False)

    pocket = relationship("Pocket", back_populates="categories")
    transactions = relationship("Transaction", back_populates="pocket_category")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    label = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(Enum(TransactionSource), default=TransactionSource.AUTRE)
    is_processed = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="transactions")
    pocket_category = relationship("Category", back_populates="transactions")
    splits = relationship("TransactionSplit", back_populates="parent_transaction")

class TransactionSplit(Base):
    """Permet de diviser une transaction entrante (Revenu) sur plusieurs destinations."""
    __tablename__ = "transaction_splits"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    pocket_id = Column(String, ForeignKey("pockets.id"), nullable=False)
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    amount = Column(Float, nullable=False)
    label = Column(String, nullable=True)

    parent_transaction = relationship("Transaction", back_populates="splits")