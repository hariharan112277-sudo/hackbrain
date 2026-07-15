"""
Stage 0 Verification Tests — Track A (Hariharan) — Dependency Layer

Run with:
    pytest tests/test_deps_stage0.py -v

Or standalone:
    python tests/test_deps_stage0.py
"""

import inspect
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
import pytest
from fastapi import HTTPException

# ── Ensure the project root is on sys.path ──────────────────────────────
sys.path.insert(0, ".")

from app.core.config import settings
from app.deps import (
    DBSession,
    UserContext,
    __all__,
    decode_token,
    get_current_user,
    get_db,
    oauth2_scheme,
    require_role,
)


# ═══════════════════════════════════════════════════════════════════════
# HELPER: Generate test JWTs
# ═══════════════════════════════════════════════════════════════════════

def _make_token(
    sub: str = "user-test",
    role: str = "admin",
    expired: bool = False,
    extra: dict | None = None,
) -> str:
    """Build a signed JWT for testing."""
    payload = {
        "sub": sub,
        "role": role,
        "type": "access",
        "exp": datetime.now(timezone.utc) + (
            timedelta(hours=-1) if expired else timedelta(hours=1)
        ),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ═══════════════════════════════════════════════════════════════════════
# 1. MODULE STRUCTURE TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestModuleStructure:
    """Verify the module exports and structure."""

    def test_all_exports_present(self):
        expected = {
            "get_db", "DBSession", "oauth2_scheme",
            "UserContext", "decode_token", "get_current_user", "require_role",
        }
        assert set(__all__) == expected

    def test_get_db_importable(self):
        assert get_db is not None
        assert callable(get_db)

    def test_dbsession_alias_exists(self):
        assert DBSession is not None

    def test_oauth2_scheme_token_url(self):
        token_url = oauth2_scheme.model.flows.password.tokenUrl
        assert token_url == "/api/v1/auth/login"

    def test_no_circular_imports_with_security_module(self):
        """deps.get_current_user and core.security.get_current_user must coexist."""
        from app.core.security import get_current_user as sec_gcu
        assert sec_gcu is not get_current_user


# ═══════════════════════════════════════════════════════════════════════
# 2. USER CONTEXT TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestUserContext:
    """Verify UserContext behaviour."""

    def test_construction(self):
        ctx = UserContext(user_id="u-1", role="admin")
        assert ctx.user_id == "u-1"
        assert ctx.role == "admin"

    def test_equality(self):
        a = UserContext("u-1", "admin")
        b = UserContext("u-1", "admin")
        assert a == b

    def test_inequality(self):
        a = UserContext("u-1", "admin")
        b = UserContext("u-2", "operator")
        assert a != b

    def test_hash(self):
        a = UserContext("u-1", "admin")
        b = UserContext("u-1", "admin")
        assert hash(a) == hash(b)
        # Usable in sets / dict keys
        s = {a, b}
        assert len(s) == 1

    def test_slots_optimisation(self):
        assert hasattr(UserContext, "__slots__")

    def test_repr(self):
        ctx = UserContext("u-1", "admin")
        r = repr(ctx)
        assert "u-1" in r and "admin" in r


# ═══════════════════════════════════════════════════════════════════════
# 3. DECODE TOKEN TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestDecodeToken:
    """Verify JWT decoding and error handling."""

    def test_valid_token(self):
        token = _make_token(sub="user-abc", role="operator")
        payload = decode_token(token)
        assert payload["sub"] == "user-abc"
        assert payload["role"] == "operator"

    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            decode_token("not.a.valid.jwt")
        assert exc_info.value.status_code == 401

    def test_expired_token_raises_401(self):
        token = _make_token(expired=True)
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == 401

    def test_bearer_header_included(self):
        """401 responses must include WWW-Authenticate: Bearer."""
        with pytest.raises(HTTPException) as exc_info:
            decode_token("bad")
        assert exc_info.value.headers.get("WWW-Authenticate") == "Bearer"


# ═══════════════════════════════════════════════════════════════════════
# 4. GET CURRENT USER TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestGetCurrentUser:
    """Verify the FastAPI dependency for current user extraction."""

    def test_signature_has_token_param(self):
        sig = inspect.signature(get_current_user)
        assert "token" in sig.parameters

    def test_returns_user_context(self):
        """When given a valid token, get_current_user should return UserContext."""
        token = _make_token(sub="u-99", role="supervisor")
        result = get_current_user(token=token)
        assert isinstance(result, UserContext)
        assert result.user_id == "u-99"
        assert result.role == "supervisor"

    def test_missing_sub_raises_401(self):
        """Token without 'sub' claim → 401."""
        payload = {
            "role": "admin",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "type": "access",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=token)
        assert exc_info.value.status_code == 401
        assert "missing required claims" in exc_info.value.detail.lower()

    def test_missing_role_raises_401(self):
        """Token without 'role' claim → 401."""
        payload = {
            "sub": "u-1",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "type": "access",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=token)
        assert exc_info.value.status_code == 401

    def test_roles_list_fallback(self):
        """Token with 'roles' list (instead of 'role' string) should extract first role."""
        payload = {
            "sub": "u-5",
            "roles": ["viewer", "operator"],
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "type": "access",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        result = get_current_user(token=token)
        assert isinstance(result, UserContext)
        assert result.user_id == "u-5"
        assert result.role == "viewer"  # First role from list


# ═══════════════════════════════════════════════════════════════════════
# 5. REQUIRE ROLE (RBAC) TESTS
# ═══════════════════════════════════════════════════════════════════════

class TestRequireRole:
    """Verify the RBAC dependency factory."""

    def test_returns_callable(self):
        checker = require_role("admin")
        assert callable(checker)

    def test_checker_signature(self):
        checker = require_role("admin", "supervisor")
        sig = inspect.signature(checker)
        assert "user" in sig.parameters

    def test_allowed_role_passes(self):
        """User with an allowed role should pass through."""
        checker = require_role("admin", "supervisor")
        admin = UserContext("u-1", "admin")
        result = checker(user=admin)
        assert result is admin

    def test_disallowed_role_raises_403(self):
        """User without an allowed role should get HTTP 403."""
        checker = require_role("admin")
        viewer = UserContext("u-2", "viewer")
        with pytest.raises(HTTPException) as exc_info:
            checker(user=viewer)
        assert exc_info.value.status_code == 403
        assert "insufficient role" in exc_info.value.detail.lower()


# ═══════════════════════════════════════════════════════════════════════
# STANDALONE RUNNER
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Quick standalone check without pytest
    passed = 0
    failed = 0
    for cls in [TestModuleStructure, TestUserContext, TestDecodeToken, TestGetCurrentUser, TestRequireRole]:
        instance = cls()
        for name in dir(instance):
            if name.startswith("test_"):
                try:
                    getattr(instance, name)()
                    print(f"  ✅ {cls.__name__}.{name}")
                    passed += 1
                except Exception as e:
                    print(f"  ❌ {cls.__name__}.{name}: {e}")
                    failed += 1

    print(f"\n{'='*60}")
    if failed == 0:
        print(f"🎉 ALL {passed} TESTS PASSED — Stage 0 verified!")
    else:
        print(f"⚠️  {failed}/{passed+failed} tests FAILED")
    print(f"{'='*60}")
    sys.exit(1 if failed else 0)
