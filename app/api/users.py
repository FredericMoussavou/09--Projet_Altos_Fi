# app/api/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.crud import user as crud_user
from app.schemas import user as schema_user
from app.core.database import get_db

router = APIRouter(prefix="/users", tags=["utilisateurs"])

@router.post("/", response_model=schema_user.UserOut)
def create_new_user(user: schema_user.UserCreate, db: Session = Depends(get_db)):
    # 1. On vérifie si l'utilisateur existe déjà
    db_user = crud_user.get_user_by_email(db, email=user.email)
    if db_user:
        # On lève une exception propre au lieu de laisser le serveur crasher
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé.")
    
    # 2. Vérification Username
    if crud_user.get_user_by_username(db, username=user.username):
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris.")
    
    # 3. Si l'email et le username sont libres, on procède à la création
    return crud_user.create_user(db=db, user_in=user)