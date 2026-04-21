from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)

def test_add_business_income():
    # 1. Création et Login
    uid = str(uuid.uuid4())[:4]
    username = f"biz_{uid}"
    client.post("/users/", json={
        "username": username, "email": f"{username}@test.fr",
        "password": "SecurePassword123!", "gender": "Homme"
    })
    login_res = client.post("/auth/login", data={"username": username, "password": "SecurePassword123!"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # 2. Enregistrement d'un revenu Business (Matière première)
    income_data = {
        "label": "Virement Client Alpha",
        "amount": 1000.0,
        "source": "Business"
    }
    res = client.post("/transactions/", json=income_data, headers=headers)
    
    assert res.status_code == 200
    data = res.json()
    assert data["amount"] == 1000.0
    assert data["source"] == "Business"
    assert data["is_processed"] is False # Doit être False par défaut

    # 3. Vérification qu'il est dans la liste des transactions à traiter
    unprocessed = client.get("/transactions/unprocessed", headers=headers)
    assert len(unprocessed.json()) == 1