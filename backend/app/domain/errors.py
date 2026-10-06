"""Erros de domínio apresentados ao usuário."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QueryError:
    code: str
    message: str
    position: int | None = None
