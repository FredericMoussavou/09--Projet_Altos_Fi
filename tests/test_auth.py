from fastapi.testclient import TestClient
from main import app
import pytest
import uuid

client = TestClient(app)

def test_complete_auth_and_password_flow():
    # 1. CRÉATION DE L'UTILISATEUR (Génération d'un email unique pour éviter les 400)
    uid = str(uuid.uuid4())[:4]
    username = f"flow_user_{uid}"
    email = f"flow_{uid}@test.fr"
    password_init = "Initial123!"
    password_new = "Nouveau123!"
    
    client.post("/users/", json={
        "username": username,
        "email": email,
        "password": password_init,
        "gender": "Homme"
    })

    # 2. LOGIN RÉUSSI (Correction de l'URL : /auth/login)
    login_res = client.post("/auth/login", data={"username": username, "password": password_init})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. LOGIN ÉCHOUÉ (MAUVAIS MOT DE PASSE)
    bad_login = client.post("/auth/login", data={"username": username, "password": "WrongPassword1!"})
    assert bad_login.status_code == 401

    # 4. CHANGEMENT DE MOT DE PASSE (Vérifie bien que ton router est /users/change-password)
    change_res = client.post(
        "/users/change-password", 
        json={"old_password": password_init, "new_password": password_new},
        headers=headers
    )
    assert change_res.status_code == 200

    # 5. TENTATIVE CONNEXION ANCIEN MOT DE PASSE (DOIT ÉCHOUER)
    old_pw_login = client.post("/auth/login", data={"username": username, "password": password_init})
    assert old_pw_login.status_code == 401

    # 6. CONNEXION NOUVEAU MOT DE PASSE (DOIT RÉUSSIR)
    new_pw_login = client.post("/auth/login", data={"username": username, "password": password_new})
    assert new_pw_login.status_code == 200
    assert "access_token" in new_pw_login.json()