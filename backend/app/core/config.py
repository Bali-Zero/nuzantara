"""Showroom settings shim — REWRITTEN, not carried.

The upstream ``backend/app/core/config.py`` (1392 lines) is not copied:
it embeds staff e-mail addresses and a phone number (SHOWROOM principle §3.3,
zero personal data). The carried modules read exactly these nine attributes
(measured 14 Oct 2026); everything else is out of scope for unit 1.
Env var names and defaults mirror upstream, except ``qdrant_timeout`` (absent
upstream -> qdrant_db falls back to 30 s; set to 10 s here per CONTRACT §8.2)
and ``environment`` (default "showroom").
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


@dataclass
class Settings:
    environment: str = field(default_factory=lambda: _env("ENVIRONMENT", "showroom"))
    embedding_provider: str = field(default_factory=lambda: _env("EMBEDDING_PROVIDER", "openai"))
    embedding_model: str = field(
        default_factory=lambda: _env("EMBEDDING_MODEL", "text-embedding-3-small")
    )
    openai_api_key: str | None = field(default_factory=lambda: _env("OPENAI_API_KEY"))
    qdrant_url: str = field(default_factory=lambda: _env("QDRANT_URL", "http://localhost:6333"))
    qdrant_default_url: str = field(
        default_factory=lambda: _env("QDRANT_DEFAULT_URL", "http://localhost:6333")
    )
    qdrant_api_key: str | None = field(default_factory=lambda: _env("QDRANT_API_KEY"))
    qdrant_timeout: int = field(default_factory=lambda: int(_env("QDRANT_TIMEOUT", "10")))
    # DEPENDENCIES §5.2: parent documents disabled -> leave DATABASE_URL unset.
    database_url: str | None = field(default_factory=lambda: _env("DATABASE_URL"))


settings = Settings()
