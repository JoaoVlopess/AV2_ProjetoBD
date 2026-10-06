"""Análise léxica da string SQL."""

from backend.app.domain.tokens import Token


class Tokenizer:
    def tokenize(self, sql: str) -> list[Token]:
        raise NotImplementedError("Implemente o tokenizador conforme o mapeamento.")
