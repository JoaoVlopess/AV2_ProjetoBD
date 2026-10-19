"""Conversão da AST para uma árvore de álgebra relacional não otimizada."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from backend.app.domain.ast_models import (
    AndExpression,
    Comparison,
    Expression,
    FieldReference,
    Literal,
    Operand,
    Query,
)


@dataclass(frozen=True, slots=True)
class Relation:
    """Tabela lida pela consulta."""

    table: str


@dataclass(frozen=True, slots=True)
class JoinOperation:
    """Junção entre dois resultados relacionais."""

    left: RelationalNode
    right: RelationalNode
    condition: Expression


@dataclass(frozen=True, slots=True)
class Selection:
    """Filtro criado a partir da cláusula WHERE."""

    source: RelationalNode
    condition: Expression


@dataclass(frozen=True, slots=True)
class Projection:
    """Escolha dos campos informados no SELECT."""

    source: RelationalNode
    fields: list[FieldReference]


RelationalNode: TypeAlias = Relation | JoinOperation | Selection | Projection


class RelationalAlgebraConverter:
    """Monta o plano na mesma ordem da SQL, sem aplicar otimizações."""

    def convert(self, query: Query) -> RelationalNode:
        current: RelationalNode = Relation(table=query.from_table)

        for join in query.joins:
            current = JoinOperation(
                left=current,
                right=Relation(table=join.table),
                condition=join.condition,
            )

        if query.where is not None:
            current = Selection(source=current, condition=query.where)

        return Projection(source=current, fields=query.fields)


class RelationalAlgebraFormatter:
    """Transforma a árvore relacional em uma expressão legível."""

    def format(self, node: RelationalNode) -> str:
        if isinstance(node, Relation):
            return node.table

        if isinstance(node, JoinOperation):
            left = self.format(node.left)
            right = self.format(node.right)
            condition = self.format_expression(node.condition)
            return f"({left} ⋈[{condition}] {right})"

        if isinstance(node, Selection):
            condition = self.format_expression(node.condition)
            return f"σ[{condition}]({self.format(node.source)})"

        fields = ", ".join(self.format_field(field) for field in node.fields)
        return f"π[{fields}]({self.format(node.source)})"

    def format_expression(self, expression: Expression) -> str:
        if isinstance(expression, Comparison):
            left = self.format_operand(expression.left)
            right = self.format_operand(expression.right)
            return f"{left} {expression.operator} {right}"

        left = self.format_expression(expression.left)
        right = self.format_expression(expression.right)
        return f"({left} AND {right})"

    def format_operand(self, operand: Operand) -> str:
        if isinstance(operand, FieldReference):
            return self.format_field(operand)

        return self.format_literal(operand)

    @staticmethod
    def format_field(field: FieldReference) -> str:
        if field.table is not None:
            return f"{field.table}.{field.name}"
        return field.name

    @staticmethod
    def format_literal(literal: Literal) -> str:
        if isinstance(literal.value, str):
            escaped_value = literal.value.replace("'", "''")
            return f"'{escaped_value}'"
        return str(literal.value)
