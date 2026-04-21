from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserGlobalOut, UserPreferencesBase, PasswordChange
from app.crud import user as crud_user
from app.api.auth import get_current_user

router = APIRouter(prefix="/users", tags=["utilisateurs"])

@router.post("/", response_model=UserOut)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    # 1. Vérification de l'email (Message exact pour le test)
    if crud_user.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
        
    # 2. Vérification du username (Pour éviter l'IntegrityError de SQLite)
    if crud_user.get_user_by_username(db, username=user.username):
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris")
        
    return crud_user.create_user(db=db, user_in=user)

@router.get("/me", response_model=UserGlobalOut)
def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me/preferences", response_model=UserPreferencesBase)
def update_my_preferences(
    new_prefs: UserPreferencesBase, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    prefs = current_user.preferences
    if not prefs:
        raise HTTPException(status_code=404, detail="Préférences non trouvées")
    
    # Mise à jour des champs [cite: 2]
    prefs.ratio_needs = new_prefs.ratio_needs
    prefs.ratio_wants = new_prefs.ratio_wants
    prefs.ratio_savings = new_prefs.ratio_savings
    prefs.ratio_give = new_prefs.ratio_give
    prefs.tithing_enabled = new_prefs.tithing_enabled
    prefs.tithing_percentage = new_prefs.tithing_percentage
    
    db.commit()
    db.refresh(prefs)
    return prefs

@router.post("/change-password")
def change_password(
    data: PasswordChange, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if not crud_user.verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Ancien mot de passe incorrect")
    crud_user.update_user_password(db, current_user, data.new_password)
    return {"message": "Mot de passe modifié avec succès"}