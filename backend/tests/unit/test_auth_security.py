from app.infrastructure.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hashing():
    hashed = hash_password("securepassword123")
    assert verify_password("securepassword123", hashed)
    assert not verify_password("wrongpassword", hashed)


def test_jwt_tokens():
    from uuid import uuid4

    user_id = uuid4()
    access = create_access_token(user_id, "test@mobius.dev")
    refresh, _ = create_refresh_token(user_id)

    access_payload = decode_token(access)
    refresh_payload = decode_token(refresh)

    assert access_payload is not None
    assert access_payload["type"] == "access"
    assert access_payload["sub"] == str(user_id)

    assert refresh_payload is not None
    assert refresh_payload["type"] == "refresh"
