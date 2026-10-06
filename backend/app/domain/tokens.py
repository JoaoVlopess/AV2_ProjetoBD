"""Tipos produzidos pelo tokenizador."""

from dataclasses import dataclass
from enum import StrEnum, auto


class TokenType(StrEnum):
    KEYWORD = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    OPERATOR = auto()
    COMMA = auto()
    DOT = auto()
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    SEMICOLON = auto()
    EOF = auto()


@dataclass(frozen=True, slots=True)
class Token:
    type: TokenType
    lexeme: str
    position: int
