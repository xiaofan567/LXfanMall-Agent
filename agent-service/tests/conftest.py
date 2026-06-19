"""Global test fixtures — environment isolation for all tests.

Every test runs with a clean set of required env vars so Settings()
never fails on import. External dependencies (Redis, Milvus, LLM API)
are NOT mocked at this layer — individual test files mock what they need.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def _env_setup(monkeypatch):
    """Force all required env vars so Settings() init never fails."""
    monkeypatch.setenv("LLM_API_KEY", "test-key-for-testing")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-16chars")
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-embedding-key")
    monkeypatch.setenv("EMBEDDING_BASE_URL", "https://test.example.com/v1")
    monkeypatch.setenv("EMBEDDING_MODEL", "test-model")
