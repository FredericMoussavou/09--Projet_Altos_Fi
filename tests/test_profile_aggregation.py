from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)

def test_get_my_complete_profile():
    # 1. Création
    uid = str(uuid.uuid4())[:4]
    email = f"agg_{uid}@test.fr"
    user_data = {
        "username": f"agg_user_{uid}",
        "email": email,
        "password": "Password123!",
        "gender": "Homme"
    }
    client.post("/users/", json=user_data)

    # 2. Login pour avoir le token
    login_res = client.post("/auth/login", data={"username": user_data["username"], "password": user_data["password"]})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Test de l'agrégation
    res = client.get("/users/me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    
    # Vérifications des "tiroirs"
    assert "profile" in data
    assert "preferences" in data
    assert data["preferences"]["ratio_needs"] == 50
    assert data["profile"]["marital_status"] == "Célibataire"