# backend/tests/unit/test_security.py
"""Tests for app.core.security — JWT creation/decoding and password hashing."""

import time

import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_subject,
    hash_password,
    verify_password,
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
)


class TestPasswordHashing:
    def test_hash_password_returns_a_different_string_than_the_input(self):
        hashed = hash_password("correct-horse-battery-staple")
        assert hashed != "correct-horse-battery-staple"

    def test_verify_password_succeeds_for_the_correct_password(self):
        hashed = hash_password("my-secret")
        assert verify_password("my-secret", hashed) is True

    def test_verify_password_fails_for_the_wrong_password(self):
        hashed = hash_password("my-secret")
        assert verify_password("wrong-password", hashed) is False

    def test_hashing_the_same_password_twice_produces_different_hashes(self):
        # bcrypt salts each hash uniquely — this guards against a
        # regression to an unsalted hashing scheme.
        assert hash_password("same-input") != hash_password("same-input")


class TestAccessToken:
    def test_create_access_token_round_trips_the_subject(self):
        token = create_access_token(subject="user-123")
        assert get_token_subject(token, expected_type=TOKEN_TYPE_ACCESS) == "user-123"

    def test_access_token_payload_includes_correct_type_claim(self):
        token = create_access_token(subject="user-123")
        payload = decode_token(token)
        assert payload["type"] == TOKEN_TYPE_ACCESS

    def test_access_token_includes_extra_claims_when_provided(self):
        token = create_access_token(subject="user-123", extra_claims={"email": "a@b.com"})
        payload = decode_token(token)
        assert payload["email"] == "a@b.com"

    def test_access_token_has_iat_and_exp_claims(self):
        token = create_access_token(subject="user-123")
        payload = decode_token(token)
        assert "iat" in payload
        assert "exp" in payload
        assert payload["exp"] > payload["iat"]


class TestRefreshToken:
    def test_create_refresh_token_round_trips_the_subject(self):
        token = create_refresh_token(subject="user-456")
        assert get_token_subject(token, expected_type=TOKEN_TYPE_REFRESH) == "user-456"

    def test_refresh_token_payload_includes_correct_type_claim(self):
        token = create_refresh_token(subject="user-456")
        payload = decode_token(token)
        assert payload["type"] == TOKEN_TYPE_REFRESH

    def test_refresh_token_expires_further_in_the_future_than_access_token(self):
        access_payload = decode_token(create_access_token(subject="u1"))
        refresh_payload = decode_token(create_refresh_token(subject="u1"))
        assert refresh_payload["exp"] > access_payload["exp"]


class TestTokenTypeEnforcement:
    def test_get_token_subject_rejects_an_access_token_when_refresh_expected(self):
        access_token = create_access_token(subject="user-123")
        with pytest.raises(JWTError, match="Expected token type 'refresh'"):
            get_token_subject(access_token, expected_type=TOKEN_TYPE_REFRESH)

    def test_get_token_subject_rejects_a_refresh_token_when_access_expected(self):
        refresh_token = create_refresh_token(subject="user-123")
        with pytest.raises(JWTError, match="Expected token type 'access'"):
            get_token_subject(refresh_token, expected_type=TOKEN_TYPE_ACCESS)


class TestTokenTampering:
    def test_decode_token_rejects_a_malformed_token_string(self):
        with pytest.raises(JWTError):
            decode_token("not.a.valid.jwt")

    def test_decode_token_rejects_a_token_signed_with_a_different_secret(self):
        from jose import jwt as jose_jwt

        forged = jose_jwt.encode({"sub": "attacker", "type": "access"}, "wrong-secret", algorithm="HS256")
        with pytest.raises(JWTError):
            decode_token(forged)

    def test_get_token_subject_raises_when_sub_claim_is_missing(self):
        from jose import jwt as jose_jwt
        from app.core.config import get_settings

        settings = get_settings()
        token_without_sub = jose_jwt.encode(
            {"type": "access"}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        with pytest.raises(JWTError, match="missing 'sub'"):
            get_token_subject(token_without_sub, expected_type=TOKEN_TYPE_ACCESS)