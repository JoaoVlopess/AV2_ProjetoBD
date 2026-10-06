"""Análise sintática dos tokens e criação da AST."""

from backend.app.domain.ast_models import Query
from backend.app.domain.tokens import Token


class Parser:
    def parse(self, tokens: list[Token]) -> Query:
        raise NotImplementedError("Implemente o parser conforme a gramática definida.")
