"""Heurísticas de seleção e projeção para o plano relacional."""

from collections.abc import Mapping

from backend.app.domain.ast_models import (
    AndExpression,
    Comparison,
    Expression,
    FieldReference,
)
from backend.app.domain.relational_algebra import (
    CartesianProduct,
    Projection,
    Relation,
    RelationalNode,
    Selection,
)

ResolvedField = tuple[str, str]
SchemaCatalog = Mapping[str, list[str]]


class RelationalAlgebraOptimizer:
    """Aplica heurísticas de seleção, projeção e ordem de junção."""

    def optimize(
        self,
        plan: RelationalNode,
        schema: SchemaCatalog,
        table_cardinalities: Mapping[str, int] | None = None,
    ) -> RelationalNode:
        self.schema = schema
        self.tables = self._relation_names(plan)
        self.table_cardinalities = dict(table_cardinalities or {})

        if not isinstance(plan, Projection):
            return self._push_selections(plan)

        source = self._push_selections(plan.source)
        source = self._reorder_joins(source)
        required_fields = self._collect_required_fields(plan.fields, source)
        if len(self._relation_names(source)) > 1:
            source = self._insert_projections(source, required_fields)

        return Projection(source=source, fields=plan.fields)

    def _push_selections(self, node: RelationalNode) -> RelationalNode:
        if isinstance(node, Selection):
            source = self._push_selections(node.source)

            # A seleção do ON representa a junção primitiva e deve
            # continuar imediatamente acima do produto cartesiano.
            if node.clause == "ON":
                return Selection(
                    source=source,
                    condition=node.condition,
                    clause="ON",
                )

            # Não atribuímos pesos diferentes a =, >, < ou <>. As condições
            # mantêm a ordem escrita no WHERE quando lidas de baixo para cima.
            conditions = self._split_and(node.condition)
            for condition in reversed(conditions):
                source = self._push_condition(source, condition)
            return source

        if isinstance(node, CartesianProduct):
            return CartesianProduct(
                left=self._push_selections(node.left),
                right=self._push_selections(node.right),
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
        if isinstance(node, CartesianProduct):
            condition_tables = self._expression_tables(condition)
            left_tables = self._relation_names(node.left)
            right_tables = self._relation_names(node.right)

            if condition_tables and condition_tables <= left_tables:
                return CartesianProduct(
                    left=self._push_condition(node.left, condition),
                    right=node.right,
                )

            if condition_tables and condition_tables <= right_tables:
                return CartesianProduct(
                    left=node.left,
                    right=self._push_condition(node.right, condition),
                )

            return Selection(source=node, condition=condition)

        if isinstance(node, Selection):
            return Selection(
                source=self._push_condition(node.source, condition),
                condition=node.condition,
                clause=node.clause,
            )

        if isinstance(node, Projection):
            return Projection(
                source=self._push_condition(node.source, condition),
                fields=node.fields,
            )

        return Selection(source=node, condition=condition)

    def _reorder_joins(self, node: RelationalNode) -> RelationalNode:
        if (
            isinstance(node, Selection)
            and node.clause == "ON"
            and isinstance(node.source, CartesianProduct)
        ):
            branches: list[RelationalNode] = []
            conditions: list[Expression] = []
            self._flatten_joins(node, branches, conditions)

            reordered_branches = [
                self._reorder_joins(branch) for branch in branches
            ]
            return self._build_join_order(reordered_branches, conditions)

        if isinstance(node, CartesianProduct):
            return CartesianProduct(
                left=self._reorder_joins(node.left),
                right=self._reorder_joins(node.right),
            )

        if isinstance(node, Selection):
            return Selection(
                source=self._reorder_joins(node.source),
                condition=node.condition,
                clause=node.clause,
            )

        if isinstance(node, Projection):
            return Projection(
                source=self._reorder_joins(node.source),
                fields=node.fields,
            )

        return node

    def _flatten_joins(
        self,
        node: RelationalNode,
        branches: list[RelationalNode],
        conditions: list[Expression],
    ) -> None:
        if (
            isinstance(node, Selection)
            and node.clause == "ON"
            and isinstance(node.source, CartesianProduct)
        ):
            self._flatten_joins(node.source.left, branches, conditions)
            self._flatten_joins(node.source.right, branches, conditions)
            conditions.append(node.condition)
            return

        branches.append(node)

    def _build_join_order(
        self,
        branches: list[RelationalNode],
        conditions: list[Expression],
    ) -> RelationalNode:
        if not branches:
            raise ValueError("Não existem relações para ordenar.")

        pending_branches = list(branches)
        pending_conditions = list(conditions)

        # A relação com menos tuplas inicia o plano. Em caso de empate,
        # preservamos a ordem original da consulta.
        start_index = min(
            range(len(pending_branches)),
            key=lambda index: (
                self._estimated_cardinality(pending_branches[index]),
                index,
            ),
        )
        current = pending_branches.pop(start_index)

        while pending_branches:
            current_tables = self._relation_names(current)
            options: list[tuple[int, int, int]] = []

            for branch_index, branch in enumerate(pending_branches):
                branch_tables = self._relation_names(branch)
                available_tables = current_tables | branch_tables

                for condition_index, condition in enumerate(pending_conditions):
                    condition_tables = self._expression_tables(condition)
                    connects_both_sides = (
                        bool(condition_tables & current_tables)
                        and bool(condition_tables & branch_tables)
                    )

                    if (
                        condition_tables <= available_tables
                        and connects_both_sides
                    ):
                        options.append(
                            (
                                self._estimated_cardinality(branch),
                                branch_index,
                                condition_index,
                            )
                        )

            if options:
                _, branch_index, condition_index = min(options)
            else:
                branch_index = min(
                    range(len(pending_branches)),
                    key=lambda index: (
                        self._estimated_cardinality(
                            pending_branches[index]
                        ),
                        index,
                    ),
                )
                condition_index = -1

            branch = pending_branches.pop(branch_index)

            if condition_index >= 0:
                condition = pending_conditions.pop(condition_index)
                product = CartesianProduct(left=current, right=branch)
                current = Selection(
                    source=product,
                    condition=condition,
                    clause="ON",
                )
            else:
                # Só ocorre quando a consulta realmente não oferece um
                # predicado capaz de conectar as duas relações.
                current = CartesianProduct(left=current, right=branch)

        for condition in pending_conditions:
            current = Selection(
                source=current,
                condition=condition,
                clause="ON",
            )

        return current

    def _estimated_cardinality(self, node: RelationalNode) -> int:
        """Estima o tamanho usando somente a quantidade de tuplas informada."""
        if isinstance(node, Relation):
            return self.table_cardinalities.get(node.table, 0)

        if isinstance(node, CartesianProduct):
            return self._estimated_cardinality(
                node.left
            ) * self._estimated_cardinality(node.right)

        # Sem estatísticas de distribuição, não inventamos pesos para
        # seleções ou projeções: elas conservam a estimativa da fonte.
        return self._estimated_cardinality(node.source)

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
        if isinstance(node, CartesianProduct):
            self._collect_operation_fields(node.left, required)
            self._collect_operation_fields(node.right, required)
            return

        if isinstance(node, Selection):
            # Uma seleção sobre uma única tabela usa seus campos antes da
            # projeção local. Eles não precisam seguir para os joins superiores.
            if (
                node.clause == "ON"
                or len(self._relation_names(node.source)) > 1
            ):
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

            # Em consultas com mais de uma relação, toda folha recebe um
            # nó de projeção explícito. Mesmo quando todos os campos da tabela
            # são necessários, a árvore deixa visível a aplicação da
            # heurística antes do produto cartesiano.
            return Projection(source=node, fields=fields)

        if isinstance(node, CartesianProduct):
            return CartesianProduct(
                left=self._insert_projections(node.left, required),
                right=self._insert_projections(node.right, required),
            )

        if isinstance(node, Selection):
            return Selection(
                source=self._insert_projections(node.source, required),
                condition=node.condition,
                clause=node.clause,
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
        if isinstance(node, CartesianProduct):
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
