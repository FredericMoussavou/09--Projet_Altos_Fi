# tests/test_auth_flow.py
from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)

def test_complete_auth_and_password_flow():
    # 1. CRÉATION DE L'UTILISATEUR
    username = "flow_user"
    password_init = "Initial123!"
    password_new = "Nouveau123!"
    
    client.post("/users/", json={
        "username": username,
        "email": "flow@test.fr",
        "password": password_init,
        "gender": "Homme"
    })

    # 2. LOGIN RÉUSSI
    login_res = client.post("/login", data={"username": username, "password": password_init})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. LOGIN ÉCHOUÉ (MAUVAIS MOT DE PASSE)
    bad_login = client.post("/login", data={"username": username, "password": "WrongPassword!"})
    assert bad_login.status_code == 401

    # 4. CHANGEMENT DE MOT DE PASSE
    # Note : On suppose ici que ta route est /users/change-password
    change_res = client.post(
        "/users/change-password", 
        json={"old_password": password_init, "new_password": password_new},
        headers=headers
    )
    assert change_res.status_code == 200

    # 5. TENTATIVE CONNEXION ANCIEN MOT DE PASSE (DOIT ÉCHOUER)
    old_pw_login = client.post("/login", data={"username": username, "password": password_init})
    assert old_pw_login.status_code == 401

    # 6. CONNEXION NOUVEAU MOT DE PASSE (DOIT RÉUSSIR)
    new_pw_login = client.post("/login", data={"username": username, "password": password_new})
    assert new_pw_login.status_code == 200
    assert "access_token" in new_pw_login.json()