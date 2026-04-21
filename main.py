# main.py
from fastapi import FastAPI
from app.core.database import engine, Base
from app.models import user
from app.api import users, auth # On importe notre nouveau fichier de routes

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Altos Fi API")

# On inclut les routes
app.include_router(auth.router)
app.include_router(users.router)

@app.get("/")
def read_root():
    return {"message": "Altos Fi est opérationnel !"}


