from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)

def create_and_login(username, email, password):
    # 1. Création de l'utilisateur
    create_res = client.post("/users/", json={
        "username": username,
        "email": email,
        "password": password,
        "gender": "Homme"
    })
    # Débuggage si la création échoue
    if create_res.status_code != 200:
        print(f"Erreur création: {create_res.json()}")
    
    # 2. Connexion
    login_res = client.post("/auth/login", data={"username": username, "password": password})
    if login_res.status_code != 200:
        print(f"Erreur login: {login_res.json()}")
        
    token = login_res.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}

def test_persona_celibataire_sans_dime():
    uid = str(uuid.uuid4())[:4]
    # Utilisation d'un mot de passe plus long et robuste
    headers = create_and_login(f"solo_{uid}", f"solo_{uid}@test.fr", "SecurePass123!")
    
    res = client.get("/users/me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    
    assert data["profile"]["marital_status"] == "Célibataire"
    # Vérification des valeurs par défaut
    assert data["preferences"]["tithing_enabled"] == True
    assert data["preferences"]["ratio_needs"] == 50

def test_persona_specifique_50_30_10_10():
    uid = str(uuid.uuid4())[:4]
    headers = create_and_login(f"spec_{uid}", f"spec_{uid}@test.fr", "SecurePass123!")
    
    # On teste la route PATCH que tu as dans ton fichier user.py 
    update_res = client.patch("/users/me/preferences", 
        json={
            "ratio_needs": 50, 
            "ratio_wants": 30, 
            "ratio_savings": 10, 
            "ratio_give": 10,
            "tithing_enabled": True,
            "tithing_percentage": 10.0
        },
        headers=headers
    )
    
    assert update_res.status_code == 200
    prefs = update_res.json()
    assert prefs["ratio_give"] == 10
    assert prefs["ratio_savings"] == 10