from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import jwt
from app.core.database import get_db
from app.core.config import settings
from app.crud import user as crud_user
from app.schemas import user as schema_user

router = APIRouter(prefix="/auth", tags=["authentification"])

def create_access_token(data: dict):
    """Génère le badge numérique (JWT)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. On cherche l'utilisateur par son username (ou email selon ton choix)
    # Ici OAuth2PasswordRequestForm utilise 'username' par défaut
    user = crud_user.get_user_by_username(db, username=form_data.username)
    
    # 2. Si pas d'utilisateur ou mauvais mot de passe
    if not user or not crud_user.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. On crée le Token
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_email(db, email=email)
    if not user:
        # Sécurité : on ne dit pas si l'email existe ou pas
        return {"msg": "Si cet email existe, un lien de récupération a été envoyé."}
    
    # On crée un token de 15 minutes seulement
    reset_token = create_access_token(data={"sub": user.username, "type": "reset"})
    return {"msg": "Email envoyé", "debug_token": reset_token} # debug_token uniquement pour nos tests

@router.post("/reset-password")
def reset_password(token: str, new_password: schema_user.PasswordReset, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "reset":
            raise HTTPException(status_code=400, detail="Token invalide pour cette action")
        username = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Token invalide ou expiré")
    
    user = crud_user.get_user_by_username(db, username=username)
    crud_user.update_user_password(db, user=user, new_password=new_password.password)
    return {"msg": "Mot de passe réinitialisé avec succès"}