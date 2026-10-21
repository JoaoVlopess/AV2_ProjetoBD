"""Heurísticas de seleção e projeção para o plano relacional."""

from collections.abc import Mapping

from backend.app.domain.ast_models import (
    AndExpression,
    Comparison,
    Expression,
    FieldReference,
)
from backend.app.domain.relational_algebra import (
    JoinOperation,
    Projection,
    Relation,
    RelationalNode,
    Selection,
)

ResolvedField = tuple[str, str]
SchemaCatalog = Mapping[str, list[str]]


class RelationalAlgebraOptimizer:
    """Reduz tuplas e atributos o mais perto possível das tabelas."""

    def optimize(
        self,
        plan: RelationalNode,
        schema: SchemaCatalog,
    ) -> RelationalNode:
        self.schema = schema
        self.tables = self._relation_names(plan)

        if not isinstance(plan, Projection):
            return self._push_selections(plan)

        source = self._push_selections(plan.source)
        required_fields = self._collect_required_fields(plan.fields, source)
        if len(self._relation_names(source)) > 1:
            source = self._insert_projections(source, required_fields)

        return Projection(source=source, fields=plan.fields)

    def _push_selections(self, node: RelationalNode) -> RelationalNode:
        if isinstance(node, Selection):
            source = self._push_selections(node.source)
            for condition in self._split_and(node.condition):
                source = self._push_condition(source, condition)
            return source

        if isinstance(node, JoinOperation):
            return JoinOperation(
                left=self._push_selections(node.left),
                right=self._push_selections(node.right),
                condition=node.condition,
            )

        if isinstance(node, Projection):
            return Projection(
                source=self._push_selections(node.source),
                fields=node.fields,
            )

        return node

    def _push_condition(
        self,
        node: RelationalNode,
        condition: Expression,
    ) -> RelationalNode:
        if isinstance(node, JoinOperation):
            condition_tables = self._expression_tables(condition)
            left_tables = self._relation_names(node.left)
            right_tables = self._relation_names(node.right)

            if condition_tables and condition_tables <= left_tables:
                return JoinOperation(
                    left=self._push_condition(node.left, condition),
                    right=node.right,
                    condition=node.condition,
                )

            if condition_tables and condition_tables <= right_tables:
                return JoinOperation(
                    left=node.left,
                    right=self._push_condition(node.right, condition),
                    condition=node.condition,
                )

            return Selection(source=node, condition=condition)

        if isinstance(node, Selection):
            return Selection(
                source=self._push_condition(node.source, condition),
                condition=node.condition,
            )

        if isinstance(node, Projection):
            return Projection(
                source=self._push_condition(node.source, condition),
                fields=node.fields,
            )

        return Selection(source=node, condition=condition)

    def _collect_required_fields(
        self,
        result_fields: list[FieldReference],
        source: RelationalNode,
    ) -> set[ResolvedField]:
        required: set[ResolvedField] = set()

        for field in result_fields:
            self._add_field(required, field)

        self._collect_operation_fields(source, required)
        return required

    def _collect_operation_fields(
        self,
        node: RelationalNode,
        required: set[ResolvedField],
    ) -> None:
        if isinstance(node, JoinOperation):
            self._add_expression_fields(required, node.condition)
            self._collect_operation_fields(node.left, required)
            self._collect_operation_fields(node.right, required)
            return

        if isinstance(node, Selection):
            # Uma seleção sobre uma única tabela usa seus campos antes da
            # projeção local. Eles não precisam seguir para os joins superiores.
            if len(self._relation_names(node.source)) > 1:
                self._add_expression_fields(required, node.condition)
            self._collect_operation_fields(node.source, required)
            return

        if isinstance(node, Projection):
            for field in node.fields:
                self._add_field(required, field)
            self._collect_operation_fields(node.source, required)

    def _insert_projections(
        self,
        node: RelationalNode,
        required: set[ResolvedField],
    ) -> RelationalNode:
        node_tables = self._relation_names(node)

        # Depois das seleções locais, conserva somente os campos necessários
        # para o SELECT final, para os JOINs e para filtros entre tabelas.
        if isinstance(node, (Relation, Selection)) and len(node_tables) == 1:
            table = next(iter(node_tables))
            fields = self._projection_fields(table, required)

            if fields and len(fields) < len(self.schema.get(table, [])):
                return Projection(source=node, fields=fields)
            return node

        if isinstance(node, JoinOperation):
            return JoinOperation(
                left=self._insert_projections(node.left, required),
                right=self._insert_projections(node.right, required),
                condition=node.condition,
            )

        if isinstance(node, Selection):
            return Selection(
                source=self._insert_projections(node.source, required),
                condition=node.condition,
            )

        if isinstance(node, Projection):
            return Projection(
                source=self._insert_projections(node.source, required),
                fields=node.fields,
            )

        return node

    def _projection_fields(
        self,
        table: str,
        required: set[ResolvedField],
    ) -> list[FieldReference]:
        required_names = {
            field_name
            for table_name, field_name in required
            if table_name == table
        }

        return [
            FieldReference(name=field_name, table=table)
            for field_name in self.schema.get(table, [])
            if field_name in required_names
        ]

    def _add_expression_fields(
        self,
        required: set[ResolvedField],
        expression: Expression,
    ) -> None:
        if isinstance(expression, Comparison):
            if isinstance(expression.left, FieldReference):
                self._add_field(required, expression.left)
            if isinstance(expression.right, FieldReference):
                self._add_field(required, expression.right)
            return

        self._add_expression_fields(required, expression.left)
        self._add_expression_fields(required, expression.right)

    def _add_field(
        self,
        required: set[ResolvedField],
        field: FieldReference,
    ) -> None:
        resolved = self._resolve_field(field)
        if resolved is not None:
            required.add(resolved)

    def _expression_tables(self, expression: Expression) -> set[str]:
        fields: set[ResolvedField] = set()
        self._add_expression_fields(fields, expression)
        return {table for table, _ in fields}

    def _resolve_field(self, field: FieldReference) -> ResolvedField | None:
        if field.table is not None:
            return field.table, field.name

        candidates = [
            table
            for table in self.tables
            if field.name in self.schema.get(table, [])
        ]
        if len(candidates) == 1:
            return candidates[0], field.name
        return None

    def _relation_names(self, node: RelationalNode) -> set[str]:
        if isinstance(node, Relation):
            return {node.table}
        if isinstance(node, JoinOperation):
            return self._relation_names(node.left) | self._relation_names(
                node.right
            )
        return self._relation_names(node.source)

    def _split_and(self, expression: Expression) -> list[Expression]:
        if isinstance(expression, AndExpression):
            return [
                *self._split_and(expression.left),
                *self._split_and(expression.right),
            ]
        return [expression]
