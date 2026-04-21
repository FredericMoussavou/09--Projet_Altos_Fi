from fastapi.testclient import TestClient
from main import app
import pytest
import uuid

client = TestClient(app)

@pytest.fixture(scope="module")
def test_user():
    """Crée des données uniques pour éviter l'erreur 400 (doublon)."""
    uid = str(uuid.uuid4())[:4]
    return {
        "username": f"user_{uid}",
        "email": f"test_{uid}@altosfi.fr",
        "password": "Initial123!",
        "gender": "Homme"
    }

def test_01_create_user(test_user):
    # Changement : on utilise le préfixe /users/
    response = client.post("/users/", json=test_user)
    assert response.status_code == 200

def test_02_login_success(test_user):
    # Changement : /login est devenu /auth/login
    response = client.post("/auth/login", data={"username": test_user["username"], "password": test_user["password"]})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_03_login_failure(test_user):
    # Changement : /auth/login
    response = client.post("/auth/login", data={"username": test_user["username"], "password": "WrongPassword1!"})
    assert response.status_code == 401

def test_04_forgot_password_flow(test_user):
    # Les routes forgot et reset sont déjà sous /auth/ dans ton code
    res_forgot = client.post(f"/auth/forgot-password?email={test_user['email']}")
    assert res_forgot.status_code == 200
    token = res_forgot.json()["debug_token"]

    # Test complexité : Trop court
    res_short = client.post(f"/auth/reset-password?token={token}", json={"password": "123"})
    assert res_short.status_code == 422

    # Reset réussi
    new_pw = "NewPassword123!"
    res_reset = client.post(f"/auth/reset-password?token={token}", json={"password": new_pw})
    assert res_reset.status_code == 200

    # Vérification connexion avec nouveau MDP sur /auth/login
    res_login = client.post("/auth/login", data={"username": test_user["username"], "password": new_pw})
    assert res_login.status_code == 200