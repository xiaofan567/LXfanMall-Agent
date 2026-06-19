"""JWT authentication dependency tests.

Source: app/api/v1/deps.py

Tests cover:
  - Bearer token extraction
  - Valid JWT parsing
  - Expired JWT rejection
  - Invalid JWT rejection
  - Missing header handling
"""

import time

import pytest
from jose import jwt

from app.api.v1.deps import CurrentUser, _extract_bearer_token, get_optional_user


# ── _extract_bearer_token ──────────────────────────────────


class TestExtractBearerToken:
    def test_valid_bearer(self):
        assert _extract_bearer_token("Bearer abc123") == "abc123"

    def test_valid_bearer_with_jwt(self):
        token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.abc"
        assert _extract_bearer_token(f"Bearer {token}") == token

    def test_no_bearer_prefix(self):
        assert _extract_bearer_token("abc123") is None

    def test_empty_string(self):
        assert _extract_bearer_token("") is None

    def test_only_prefix(self):
        # "Bearer " with nothing after → empty string (not None)
        assert _extract_bearer_token("Bearer ") == ""

    def test_wrong_prefix(self):
        assert _extract_bearer_token("Token abc123") is None

    def test_lowercase_bearer(self):
        # should not match (case-sensitive)
        assert _extract_bearer_token("bearer abc123") is None


# ── get_optional_user ──────────────────────────────────────


class TestGetOptionalUser:
    @pytest.mark.asyncio
    async def test_no_header_returns_none(self):
        result = await get_optional_user(authorization=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_token_returns_none(self):
        result = await get_optional_user(authorization="Bearer invalid.token.here")
        assert result is None

    @pytest.mark.asyncio
    async def test_expired_token_returns_none(self):
        payload = {"sub": "testuser", "exp": int(time.time()) - 3600}
        token = jwt.encode(payload, "secret", algorithm="HS256")
        result = await get_optional_user(authorization=f"Bearer {token}")
        assert result is None

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self):
        payload = {"sub": "testuser", "exp": int(time.time()) + 3600}
        token = jwt.encode(payload, "secret", algorithm="HS256")
        result = await get_optional_user(authorization=f"Bearer {token}")
        assert result is not None
        assert result.username == "testuser"
        assert result.token == token

    @pytest.mark.asyncio
    async def test_no_sub_returns_none(self):
        """JWT without 'sub' claim should return None."""
        payload = {"exp": int(time.time()) + 3600, "name": "test"}
        token = jwt.encode(payload, "secret", algorithm="HS256")
        result = await get_optional_user(authorization=f"Bearer {token}")
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_sub_returns_none(self):
        """JWT with empty 'sub' should return None."""
        payload = {"sub": "", "exp": int(time.time()) + 3600}
        token = jwt.encode(payload, "secret", algorithm="HS256")
        result = await get_optional_user(authorization=f"Bearer {token}")
        assert result is None

    @pytest.mark.asyncio
    async def test_no_exp_is_valid(self):
        """JWT without 'exp' claim should be accepted (no expiry check)."""
        payload = {"sub": "testuser"}
        token = jwt.encode(payload, "secret", algorithm="HS256")
        result = await get_optional_user(authorization=f"Bearer {token}")
        assert result is not None
        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_returns_current_user_type(self):
        payload = {"sub": "alice", "exp": int(time.time()) + 3600}
        token = jwt.encode(payload, "secret", algorithm="HS256")
        result = await get_optional_user(authorization=f"Bearer {token}")
        assert isinstance(result, CurrentUser)
        assert result.username == "alice"


# ── CurrentUser dataclass ─────────────────────────────────


class TestCurrentUser:
    def test_fields(self):
        user = CurrentUser(username="test", token="tok123")
        assert user.username == "test"
        assert user.token == "tok123"
