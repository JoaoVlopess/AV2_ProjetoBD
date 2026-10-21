"""Modelos de resultado usados entre o domínio e a aplicação."""

from dataclasses import dataclass, field
from typing import Any

from backend.app.domain.ast_models import Query
from backend.app.domain.errors import QueryError
from backend.app.domain.tokens import Token


@dataclass(slots=True)
class QueryAnalysisResult:
    valid: bool
    tokens: list[Token] = field(default_factory=list)
    query: Query | None = None
    errors: list[QueryError] = field(default_factory=list)
    algebra: str | None = None
    graph: dict[str, Any] | None = None
    optimized_algebra: str | None = None
    optimized_graph: dict[str, Any] | None = None
