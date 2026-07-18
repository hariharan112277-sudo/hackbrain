"""Regression coverage for the production-ready architectural migration."""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.core import security
from app.core.config import Settings, settings
from app.core.dependencies import (
    get_user_repository,
    initialize_production_repositories,
    initialize_stub_repositories,
    reset_repository_subsystem,
)
from app.repositories.production import SQLAlchemyUserRepository


PRODUCTION_SECRET = "production-secret-key-with-more-than-thirty-two-characters"
PRODUCTION_DATABASE = "postgresql+psycopg2://iob:password@db.example/iob"


def test_password_module_exports_only_unified_password_helpers():
    assert security.__all__ == ["hash_password", "verify_password"]
    legacy_name = "get_" + "password_hash"
    assert not hasattr(security, legacy_name)


def test_production_allows_empty_mqtt_credentials_when_explicitly_unset():
    # MQTT_PASSWORD is optional in the current Settings model; production
    # boots without it (the bridge will degrade gracefully when no broker
    # is configured). Verify the settings object still constructs cleanly
    # and reports production mode.
    configured = Settings(
        ENV="production",
        SECRET_KEY=PRODUCTION_SECRET,
        DATABASE_URL=PRODUCTION_DATABASE,
        MQTT_PASSWORD=None,
        USE_STUB_REPOSITORIES=False,
        _env_file=None,
    )
    assert configured.is_production is True


def test_production_rejects_missing_database_url():
    with pytest.raises(PydanticValidationError, match="DATABASE_URL"):
        Settings(
            ENV="production",
            SECRET_KEY=PRODUCTION_SECRET,
            DATABASE_URL="",
            MQTT_PASSWORD="mqtt-secret",
            USE_STUB_REPOSITORIES=False,
            _env_file=None,
        )


def test_production_accepts_explicit_secrets_and_persistent_strategy():
    configured = Settings(
        ENV="production",
        SECRET_KEY=PRODUCTION_SECRET,
        DATABASE_URL=PRODUCTION_DATABASE,
        MQTT_PASSWORD="mqtt-secret",
        USE_STUB_REPOSITORIES=False,
        _env_file=None,
    )
    assert configured.is_production is True


def test_stub_initialization_is_blocked_in_production():
    previous_env = settings.ENV
    previous_environment = settings.ENVIRONMENT
    try:
        settings.ENV = "production"
        settings.ENVIRONMENT = "production"
        reset_repository_subsystem()
        with pytest.raises(RuntimeError, match="forbidden in production"):
            initialize_stub_repositories()
    finally:
        settings.ENV = previous_env
        settings.ENVIRONMENT = previous_environment
        reset_repository_subsystem()


def test_persistent_strategy_binds_a_real_user_adapter():
    previous_values = {
        "ENV": settings.ENV,
        "ENVIRONMENT": settings.ENVIRONMENT,
        "USE_STUB_REPOSITORIES": settings.USE_STUB_REPOSITORIES,
    }
    try:
        settings.ENV = "test"
        settings.ENVIRONMENT = "test"
        settings.USE_STUB_REPOSITORIES = False
        reset_repository_subsystem()
        initialize_production_repositories()

        from app.core.dependencies import get_user_repo

        assert isinstance(get_user_repo(), SQLAlchemyUserRepository)
    finally:
        reset_repository_subsystem()
        for name, value in previous_values.items():
            setattr(settings, name, value)


@pytest.mark.asyncio
async def test_fastapi_user_provider_never_yields_none():
    previous_values = {
        "ENV": settings.ENV,
        "ENVIRONMENT": settings.ENVIRONMENT,
        "USE_STUB_REPOSITORIES": settings.USE_STUB_REPOSITORIES,
    }
    try:
        settings.ENV = "test"
        settings.ENVIRONMENT = "test"
        settings.USE_STUB_REPOSITORIES = True
        reset_repository_subsystem()
        initialize_stub_repositories()
        provider = get_user_repository()
        repository = await anext(provider)
        assert repository is not None
        await provider.aclose()
    finally:
        reset_repository_subsystem()
        for name, value in previous_values.items():
            setattr(settings, name, value)
