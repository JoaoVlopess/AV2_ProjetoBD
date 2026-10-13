"""Análise léxica da string SQL."""

import re
from backend.app.domain.tokens import Token, TokenType


KEYWORDS = frozenset(
    {
        "SELECT",
        "FROM",
        "WHERE",
        "INNER",
        "JOIN",
        "ON",
        "AND",
    }
)

SYMBOLS = {
    ",": TokenType.COMMA,
    ".": TokenType.DOT,
    "(": TokenType.LEFT_PAREN,
    ")": TokenType.RIGHT_PAREN,
    ";": TokenType.SEMICOLON,
}


class Tokenizer:

    def _classify(self, lexeme: str) -> TokenType:
        normalized = lexeme.upper()

        if normalized in KEYWORDS:
            return TokenType.KEYWORD

        if lexeme in SYMBOLS:
            return SYMBOLS[lexeme]

        if lexeme in {"=", ">", "<", "<=", ">=", "<>"}:
            return TokenType.OPERATOR

        if re.fullmatch(r"\d+(\.\d+)?", lexeme):
            return TokenType.NUMBER

        if lexeme.startswith("'") and lexeme.endswith("'"):
            return TokenType.STRING

        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", lexeme):
            return TokenType.IDENTIFIER

        raise ValueError(f"Token desconhecido: {lexeme}")
    

    def tokenize(self, sql: str) -> list[Token]:
        pattern = r"'[^']*'|\d+(?:\.\d+)?|<=|>=|<>|[=<>]|[A-Za-z_][A-Za-z0-9_]*|[,.();]"
        
        tokens = []

        cursor = 0
        
        # O finditer acha todas as correspondências na string original sem quebrar os espaços
        for match in re.finditer(pattern, sql):

            lexeme = match.group()
            position = match.start() # Pega a posição real do caractere na string original!
            
            token_type = self._classify(lexeme)

            skipped = sql[cursor:match.start()]

            if skipped.strip():
                invalid_position = cursor + len(skipped) - len(skipped.lstrip())
                raise ValueError(
                    f"Caractere inesperado na posição {invalid_position}"
                )
            
            tokens.append(
                Token(
                    type=token_type,
                    lexeme=lexeme,
                    position=position
                )
            )

            cursor = match.end()

        remaining = sql[cursor:]

        if remaining.strip():
            raise ValueError(f"Texto inválido na posição {cursor}")
        
        tokens.append(
            Token(
                type=TokenType.EOF,
                lexeme="",
                position=len(sql),
            )
        )
        
        return tokens
    

