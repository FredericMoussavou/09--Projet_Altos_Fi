import pytest
from pydantic import ValidationError
from app.schemas.user import UserPreferencesBase, UserCreate

def test_ratios_sum_validation():
    # Test valide
    pref = UserPreferencesBase(ratio_needs=50, ratio_wants=20, ratio_savings=20, ratio_give=10)
    assert pref.ratio_needs + pref.ratio_wants + pref.ratio_savings + pref.ratio_give == 100

    # Test invalide (Total 110)
    with pytest.raises(ValidationError) as excinfo:
        UserPreferencesBase(ratio_needs=60, ratio_wants=30, ratio_savings=20, ratio_give=0)
    assert "La somme des ratios doit être égale à 100" in str(excinfo.value)

def test_password_complexity_validation():
    # Test invalide (Pas de majuscule)
    with pytest.raises(ValidationError):
        UserCreate(username="test", email="t@t.com", password="password123!")

    # Test valide
    user = UserCreate(username="test", email="t@t.com", password="Password123!")
    assert user.password == "Password123!"