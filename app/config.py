"""
Application Settings — Compatibility Alias
Track A (Database Layer / Stage 1)

The canonical settings object for this project lives in ``app.core.config``
(Phase 5 configuration module). Track A's database layer imports settings via
``from app.config import settings`` as mandated by the Stage 1 specification.

This module is a thin re-export shim so BOTH import paths resolve to the exact
same cached ``Settings`` instance — no duplicate config, no behavior change:

    from app.config import settings        # Track A path (this module)
    from app.core.config import settings   # existing Phase 5 path

Do NOT add new configuration here. Extend ``app.core.config.Settings`` instead.
"""

from app.core.config import Settings, get_settings, settings

__all__ = ["Settings", "get_settings", "settings"]
