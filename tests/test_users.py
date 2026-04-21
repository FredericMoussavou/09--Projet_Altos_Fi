# tests/test_users.py
from fastapi.testclient import TestClient
from main import app
import pytest
import uuid

client = TestClient(app)

# Fonction utilitaire pour générer des données valides rapidement
def get_valid_user_data():
    uid = str(uuid.uuid4())[:8]
    return {
        "username": f"user_{uid}",
        "email": f"test_{uid}@altosfi.fr",
        "password": "Password123!",
        "first_name": "Test",
        "last_name": "User",
        "gender": "Homme",
        "is_dime_enabled": False
    }

# --- TESTS DE SUCCÈS ---

def test_create_user_success():
    """Vérifie qu'un utilisateur totalement valide est accepté."""
    data = get_valid_user_data()
    response = client.post("/users/", json=data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["username"] == data["username"]
    assert "id" in res_json
    assert "password" not in res_json  # Sécurité : ne jamais renvoyer le MDP

# --- TESTS SUR LE USERNAME ---

def test_username_too_short():
    data = get_valid_user_data()
    data["username"] = "ab" # min_length=3
    response = client.post("/users/", json=data)
    assert response.status_code == 422

def test_username_too_long():
    data = get_valid_user_data()
    data["username"] = "a" * 21 # max_length=20
    response = client.post("/users/", json=data)
    assert response.status_code == 422

# --- TESTS SUR L'EMAIL ---

def test_invalid_email_format():
    data = get_valid_user_data()
    data["email"] = "pas-un-email"
    response = client.post("/users/", json=data)
    assert response.status_code == 422

# --- TESTS SUR LE MOT DE PASSE (COMPLEXITÉ) ---

@pytest.mark.parametrize("bad_password", [
    "short1!",       # Trop court (< 8)
    "toutminuscule1!", # Pas de majuscule
    "TOUTMAJUSCULE1!", # Pas de minuscule
    "Password!!",     # Pas de chiffre
    "Password123",    # Pas de caractère spécial
])
def test_password_complexity_rules(bad_password):
    data = get_valid_user_data()
    data["password"] = bad_password
    response = client.post("/users/", json=data)
    assert response.status_code == 422

# --- TESTS SUR LE GENRE (ENUM) ---

def test_invalid_gender():
    data = get_valid_user_data()
    data["gender"] = "Robot" # Pas dans l'Enum
    response = client.post("/users/", json=data)
    assert response.status_code == 422

# --- TESTS DE DOUBLONS (BORDURES DE LOGIQUE) ---

def test_duplicate_username():
    # On crée un premier utilisateur
    data1 = get_valid_user_data()
    client.post("/users/", json=data1)
    
    # On tente de créer un second avec le même username mais email différent
    data2 = get_valid_user_data()
    data2["username"] = data1["username"]
    response = client.post("/users/", json=data2)
    assert response.status_code == 400
    assert "nom d'utilisateur est déjà pris" in response.json()["detail"]

def test_duplicate_email():
    # On crée un premier utilisateur
    data1 = get_valid_user_data()
    client.post("/users/", json=data1)
    
    # On tente de créer un second avec le même email mais username différent
    data2 = get_valid_user_data()
    data2["email"] = data1["email"]
    response = client.post("/users/", json=data2)
    assert response.status_code == 400
    assert "email est déjà utilisé" in response.json()["detail"]