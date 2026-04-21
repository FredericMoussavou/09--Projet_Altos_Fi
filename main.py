# main.py
from fastapi import FastAPI
from app.core.database import engine, Base
from app.models import user
from app.api import users # On importe notre nouveau fichier de routes

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Altos Fi API")

# On inclut les routes utilisateurs
app.include_router(users.router)

@app.get("/")
def read_root():
    return {"message": "Altos Fi est opérationnel !"}