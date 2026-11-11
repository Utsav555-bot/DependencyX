import pytest
from backend.app.core.security import get_password_hash, verify_password, create_access_token, decode_token

def test_password_hashing():
    raw_password = "SuperSecurePassword123!"
    hashed = get_password_hash(raw_password)
    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

def test_jwt_token_creation_and_decoding():
    user_id = "usr_test_123"
    role = "admin"
    org_id = "org_test_456"

    token = create_access_token(subject=user_id, role=role, org_id=org_id)
    assert isinstance(token, str)
    assert len(token) > 20

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["org_id"] == org_id
    assert "exp" in payload
