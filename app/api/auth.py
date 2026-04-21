from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import jwt # On garde ta bibliothèque actuelle
from app.core.database import get_db
from app.core.config import settings
from app.crud import user as crud_user
from app.schemas import user as schema_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["authentification"])

# Indique à FastAPI où aller chercher le token pour les routes protégées
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# --- UTILITAIRES ---

def create_access_token(data: dict):
    """Génère le badge numérique (JWT)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# --- LE GARDE DU CORPS (La fonction qui manquait) ---

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """Vérifie le token et renvoie l'utilisateur actuel."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expirée ou invalide",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = crud_user.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user

# --- ROUTES AUTH ---

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud_user.get_user_by_username(db, username=form_data.username)
    
    if not user or not crud_user.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_email(db, email=email)
    if not user:
        return {"msg": "Si cet email existe, un lien de récupération a été envoyé."}
    
    reset_token = create_access_token(data={"sub": user.username, "type": "reset"})
    return {"msg": "Email envoyé", "debug_token": reset_token}

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
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
    crud_user.update_user_password(db, user=user, new_password=new_password.password)
    return {"msg": "Mot de passe réinitialisé avec succès"}