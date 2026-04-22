from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)

def test_allocation_calculation_logic():
    # 1. Setup User avec ratios 50/30/10/10 (Needs/Wants/Savings/Give) et Dîme 10%
    uid = str(uuid.uuid4())[:4]
    username = f"engine_{uid}"
    client.post("/users/", json={
        "username": username, "email": f"{username}@test.fr",
        "password": "SecurePassword123!", "gender": "Homme"
    })
    login_res = client.post("/auth/login", data={"username": username, "password": "SecurePassword123!"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}
    
    # 2. Création d'un revenu de 1000€
    inc = client.post("/transactions/", headers=headers, json={
        "label": "Salaire Test", "amount": 1000.0, "source": "Salaire"
    }).json()
    
    # 3. Lancement de l'allocation
    res = client.post(f"/transactions/{inc['id']}/allocate", headers=headers)
    assert res.status_code == 200
    alloc = res.json()["allocation"]
    
    # VÉRIFICATION OPTION B (1000€ brut)
    # 1. Dîme 10% = 100€
    # 2. Reste = 900€
    # 3. Needs (50% de 900) = 450€
    # 4. Wants (30% de 900) = 270€
    assert alloc["tithe"] == 100.0
    assert alloc["needs"] == 450.0
    assert alloc["wants"] == 270.0
    assert (alloc["tithe"] + alloc["needs"] + alloc["wants"] + alloc["savings"] + alloc["extra_give"]) == 1000.0