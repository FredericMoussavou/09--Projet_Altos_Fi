from fastapi import FastAPI
from app.core.database import engine, Base
from app.models import user
from app.api import users, auth, transactions, budget# Ajout de transactions


# Création des tables au démarrage (incluant la nouvelle table transactions)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Altos Fi API")

# On inclut les routes
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(transactions.router) # Activation du nouveau routeur
app.include_router(budget.router)

@app.get("/")
def read_root():
    return {"message": "Altos Fi est opérationnel !"}


