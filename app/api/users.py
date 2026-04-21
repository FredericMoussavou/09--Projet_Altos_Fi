# app/api/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.crud import user as crud_user
from app.api.deps import get_current_user
from app.models.user import User
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

@router.post("/change-password")
def change_password(
    passwords: schema_user.PasswordChange, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Vérification de l'ancien mot de passe
    if not crud_user.verify_password(passwords.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=400, 
            detail="L'ancien mot de passe est incorrect."
        )
    
    # 2. Vérification que le nouveau mot de passe est différent de l'ancien
    if passwords.old_password == passwords.new_password:
        raise HTTPException(
            status_code=400, 
            detail="Le nouveau mot de passe doit être différent de l'ancien."
        )
    
    # 3. Mise à jour via le CRUD
    crud_user.update_user_password(db, user=current_user, new_password=passwords.new_password)
    
    return {"msg": "Mot de passe modifié avec succès."}