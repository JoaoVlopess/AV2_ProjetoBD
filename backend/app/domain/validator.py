"""Validação semântica de tabelas, campos e ambiguidades."""

from backend.app.domain.ast_models import Query
from backend.app.domain.errors import QueryError


class QueryValidator:
    def validate(
        self,
        query: Query,
        catalog: dict[str, list[str]],
    ) -> list[QueryError]:
        raise NotImplementedError("Implemente as validações semânticas.")
