# app/core/database.py
from sqlalchemy import create_engine
# On change l'import ici pour suivre la version 2.0
from sqlalchemy.orm import sessionmaker, declarative_base 

SQLALCHEMY_DATABASE_URL = "sqlite:///./altos_fi.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# On utilise la nouvelle syntaxe recommandée
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()