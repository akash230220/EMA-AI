# backend/tests/unit/test_config.py
"""Tests for app.core.config.Settings — the parsing/validation logic, not the raw env values themselves."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


class TestCorsOriginsParsing:
    def test_parses_comma_separated_origins_into_list(self):
        s = Settings(CORS_ALLOWED_ORIGINS="http://localhost:5173,https://app.example.com")
        assert s.CORS_ALLOWED_ORIGINS == ["http://localhost:5173", "https://app.example.com"]

    def test_strips_whitespace_around_each_origin(self):
        s = Settings(CORS_ALLOWED_ORIGINS=" http://a.com , http://b.com ")
        assert s.CORS_ALLOWED_ORIGINS == ["http://a.com", "http://b.com"]

    def test_single_origin_still_returns_a_list(self):
        s = Settings(CORS_ALLOWED_ORIGINS="http://localhost:5173")
        assert s.CORS_ALLOWED_ORIGINS == ["http://localhost:5173"]

    def test_empty_string_returns_empty_list_not_list_with_empty_string(self):
        s = Settings(CORS_ALLOWED_ORIGINS="")
        assert s.CORS_ALLOWED_ORIGINS == []


class TestGoogleOAuthScopesParsing:
    def test_parses_space_separated_scopes_into_list(self):
        s = Settings(GOOGLE_OAUTH_SCOPES="openid email profile")
        assert s.GOOGLE_OAUTH_SCOPES == ["openid", "email", "profile"]

    def test_collapses_multiple_spaces(self):
        s = Settings(GOOGLE_OAUTH_SCOPES="openid   email")
        assert s.GOOGLE_OAUTH_SCOPES == ["openid", "email"]


class TestEnvironmentValidation:
    @pytest.mark.parametrize("valid_env", ["development", "staging", "production"])
    def test_accepts_valid_environment_values(self, valid_env):
        s = Settings(ENVIRONMENT=valid_env)
        assert s.ENVIRONMENT == valid_env

    def test_rejects_invalid_environment_value(self):
        with pytest.raises(ValidationError):
            Settings(ENVIRONMENT="not-a-real-environment")

    def test_is_production_true_only_when_environment_is_production(self):
        assert Settings(ENVIRONMENT="production").is_production is True
        assert Settings(ENVIRONMENT="development").is_production is False
        assert Settings(ENVIRONMENT="staging").is_production is False


class TestDefaults:
    def test_default_jwt_algorithm_is_hs256(self):
        assert Settings().JWT_ALGORITHM == "HS256"

    def test_default_access_token_expiry_is_30_minutes(self):
        assert Settings().ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_default_rate_limit_is_120_per_minute(self):
        assert Settings().RATE_LIMIT_PER_MINUTE == 120