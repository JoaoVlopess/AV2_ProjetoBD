"""Árvore sintática abstrata da consulta aceita pelo projeto."""

from dataclasses import dataclass, field
from typing import TypeAlias


@dataclass(frozen=True, slots=True)
class FieldReference:
    name: str
    table: str | None = None


@dataclass(frozen=True, slots=True)
class Literal:
    value: str | int | float


Operand: TypeAlias = FieldReference | Literal


@dataclass(frozen=True, slots=True)
class Comparison:
    left: Operand
    operator: str
    right: Operand


@dataclass(frozen=True, slots=True)
class AndExpression:
    left: "Expression"
    right: "Expression"


Expression: TypeAlias = Comparison | AndExpression


@dataclass(frozen=True, slots=True)
class Join:
    table: str
    condition: Expression


@dataclass(frozen=True, slots=True)
class Query:
    fields: list[FieldReference]
    from_table: str
    joins: list[Join] = field(default_factory=list)
    where: Expression | None = None
