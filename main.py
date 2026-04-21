# main.py
from fastapi import FastAPI
from app.core.database import engine, Base
from app.models import user # On importe le modèle pour que SQLAlchemy le voie

# Cette ligne est magique : elle parcourt tous les modèles héritant de "Base"
# et crée les tables dans la base de données si elles n'existent pas encore.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Altos Fi API")

@app.get("/")
def read_root():
    return {"message": "Altos Fi est opérationnel !"}