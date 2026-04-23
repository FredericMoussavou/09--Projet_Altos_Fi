import uuid
import enum
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Integer, DateTime, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

# Enums pour la cohérence des données
class CategoryType(str, enum.Enum):
    FIXED = "fixed"
    VARIABLE = "variable"

class TransactionSource(str, enum.Enum):
    MANUAL = "MANUAL"
    IMPORT = "IMPORT"
    SYSTEM = "SYSTEM"
    AUTRE = "AUTRE"

class DebtStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"

class SavingType(str, enum.Enum):
    PRECAUTION = "precaution" # Matelas de sécurité
    PROJECT = "project"       # Ex: Projet Porte 4000€

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)

    settings = relationship("UserSettings", back_populates="user", uselist=False)
    pockets = relationship("Pocket", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")

class Pocket(Base):
    __tablename__ = "pockets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    user_id = Column(String, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="pockets")
    categories = relationship("Category", back_populates="pocket")

class Category(Base):
    __tablename__ = "categories"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    pocket_id = Column(String, ForeignKey("pockets.id"))
    # Nouveau : Type de dépense
    type = Column(Enum(CategoryType), default=CategoryType.VARIABLE)
    
    pocket = relationship("Pocket", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")
    budgets = relationship("Budget", back_populates="category")
    debts = relationship("Debt", back_populates="category")

class Budget(Base):
    __tablename__ = "budgets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id = Column(String, ForeignKey("categories.id"))
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    estimated_amount = Column(Float, default=0.0)
    # On stocke le réalisé final ici à la clôture du mois
    final_actual_amount = Column(Float, nullable=True) 
    alert_threshold = Column(Float, default=0.2)
    is_alert_enabled = Column(Boolean, default=True)
    
    category = relationship("Category", back_populates="budgets")

class Debt(Base):
    __tablename__ = "debts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id = Column(String, ForeignKey("categories.id"))
    name = Column(String, nullable=False) # Ex: Crédit Auto Tesla
    total_capital = Column(Float, nullable=False)
    monthly_installment = Column(Float, nullable=False)
    remaining_balance = Column(Float, nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    status = Column(Enum(DebtStatus), default=DebtStatus.ACTIVE)
    
    category = relationship("Category", back_populates="debts")

class Saving(Base):
    __tablename__ = "savings"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String, nullable=False) # Ex: Projet Porte
    type = Column(Enum(SavingType), default=SavingType.PROJECT)
    target_amount = Column(Float, default=0.0)
    current_amount = Column(Float, default=0.0)
    monthly_contribution = Column(Float, default=0.0)
    
    user = relationship("User")

# --- Modèles existants conservés ---
class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    label = Column(String)
    amount = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    splits = relationship("TransactionSplit", back_populates="transaction")

class TransactionSplit(Base):
    __tablename__ = "transaction_splits"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String, ForeignKey("transactions.id"))
    pocket_id = Column(String, ForeignKey("pockets.id"))
    amount = Column(Float)
    
    transaction = relationship("Transaction", back_populates="splits")

class UserSettings(Base):
    __tablename__ = "user_settings"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), unique=True)
    tithing_enabled = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="settings")