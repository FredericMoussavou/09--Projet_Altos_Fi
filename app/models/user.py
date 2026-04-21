# app/models/user.py
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.core.database import Base # On créera ce fichier juste après

class User(Base):
    __tablename__ = "users"

    # Identifiant unique (UUID) pour plus de sécurité
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Données d'identification
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    # Identité civile
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    gender = Column(String, nullable=True) # On pourra affiner avec un Enum plus tard
    phone_number = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    
    # Paramètres Altos Fi
    is_dime_enabled = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)