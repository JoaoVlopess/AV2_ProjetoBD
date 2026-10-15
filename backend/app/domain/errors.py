"""Erros de domínio apresentados ao usuário."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QueryError:
    code: str
    message: str
    position: int | None = None


class QueryLexicalError(Exception):
    def __init__(self, message: str, position: int):
        super().__init__(message)
        self.message = message
        self.position = position


class QuerySyntaxError(Exception):
    def __init__(self, message: str, position: int):
        super().__init__(message)
        self.message = message
        self.position = position
