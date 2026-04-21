from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.crud import user as crud_user
from app.models.user import User

# On indique à FastAPI où aller chercher le Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    try:
        # 1. On décode le Token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token invalide")
    except (jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    # 2. On vérifie que l'utilisateur existe toujours en base
    user = crud_user.get_user_by_username(db, username=username)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    return user