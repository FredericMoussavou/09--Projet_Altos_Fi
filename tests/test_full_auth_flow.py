from fastapi.testclient import TestClient
from main import app
import pytest
import uuid

client = TestClient(app)

@pytest.fixture
def unique_user():
    uid = str(uuid.uuid4())[:4]
    return {
        "username": f"user_{uid}",
        "email": f"test_{uid}@altosfi.fr",
        "password": "SecurePassword123!",
        "first_name": "Test",
        "last_name": "User",
        "gender": "Homme"
    }

def test_complete_flow(unique_user):
    # 1. Création d'utilisateur
    res_create = client.post("/users/", json=unique_user)
    assert res_create.status_code == 200
    
    # 2. Login
    res_login = client.post("/auth/login", data={
        "username": unique_user["username"], 
        "password": unique_user["password"]
    })
    assert res_login.status_code == 200
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Accès protégé (Verification de l'identité)
    # Note: On testera /users/me une fois la route créée, 
    # pour l'instant on vérifie juste que le login renvoie un token valide.
    assert token is not None

def test_password_reset_flow(unique_user):
    # Création préalable
    client.post("/users/", json=unique_user)
    
    # Demande de reset
    res_forgot = client.post(f"/auth/forgot-password?email={unique_user['email']}")
    assert res_forgot.status_code == 200
    debug_token = res_forgot.json()["debug_token"]
    
    # Reset avec nouveau MDP
    new_pw = "NewSecret456!"
    res_reset = client.post(f"/auth/reset-password?token={debug_token}", json={"password": new_pw})
    assert res_reset.status_code == 200
    
    # Vérification nouvelle connexion
    res_login = client.post("/auth/login", data={
        "username": unique_user["username"], 
        "password": new_pw
    })
    assert res_login.status_code == 200