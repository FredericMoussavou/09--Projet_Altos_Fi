import os
from datetime import timedelta

class Settings:
    PROJECT_NAME: str = "Altos Fi"
    # DANS LA VRAIE VIE : utiliser une variable d'environnement
    SECRET_KEY: str = "UNE_CLE_TRES_SECRETE_ET_LONGUE_A_CHANGER_EN_PROD"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # Le badge dure 24h

settings = Settings()