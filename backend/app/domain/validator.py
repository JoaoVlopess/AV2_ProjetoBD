"""Validação semântica de tabelas, campos e ambiguidades."""

from backend.app.domain.ast_models import (
    AndExpression,
    Comparison,
    Expression,
    FieldReference,
    Query,
)
from backend.app.domain.errors import QueryError


class QueryValidator:
    def _validate_field(
        self,
        field: FieldReference,
        table_names: dict[str, str],
        fields_by_table: dict[str, set[str]],
        query_tables: set[str],
    ) -> list[QueryError]:
        field_name = field.name.casefold()

        if field.table is not None:
            table_name = field.table.casefold()

            if table_name not in table_names:
                return [
                    QueryError(
                        code="UNKNOWN_TABLE",
                        message=f'A tabela "{field.table}" não existe.',
                    )
                ]

            if table_name not in query_tables:
                return [
                    QueryError(
                        code="TABLE_NOT_IN_QUERY",
                        message=(
                            f'A tabela "{field.table}" não participa da consulta.'
                        ),
                    )
                ]

            if field_name not in fields_by_table[table_name]:
                return [
                    QueryError(
                        code="UNKNOWN_FIELD",
                        message=(
                            f'O campo "{field.table}.{field.name}" não existe.'
                        ),
                    )
                ]

            return []

        matching_tables = [
            table_name
            for table_name in query_tables
            if table_name in fields_by_table
            and field_name in fields_by_table[table_name]
        ]

        if not matching_tables:
            return [
                QueryError(
                    code="UNKNOWN_FIELD",
                    message=(
                        f'O campo "{field.name}" não existe nas tabelas da consulta.'
                    ),
                )
            ]

        if len(matching_tables) > 1:
            return [
                QueryError(
                    code="AMBIGUOUS_FIELD",
                    message=(
                        f'O campo "{field.name}" é ambíguo; informe a tabela.'
                    ),
                )
            ]

        return []

    def _validate_expression(
        self,
        expression: Expression,
        table_names: dict[str, str],
        fields_by_table: dict[str, set[str]],
        query_tables: set[str],
    ) -> list[QueryError]:
        if isinstance(expression, Comparison):
            errors: list[QueryError] = []

            if isinstance(expression.left, FieldReference):
                errors.extend(
                    self._validate_field(
                        expression.left,
                        table_names,
                        fields_by_table,
                        query_tables,
                    )
                )

            if isinstance(expression.right, FieldReference):
                errors.extend(
                    self._validate_field(
                        expression.right,
                        table_names,
                        fields_by_table,
                        query_tables,
                    )
                )

            return errors

        if isinstance(expression, AndExpression):
            return self._validate_expression(
                expression.left,
                table_names,
                fields_by_table,
                query_tables,
            ) + self._validate_expression(
                expression.right,
                table_names,
                fields_by_table,
                query_tables,
            )

        return []

    def validate(
        self,
        query: Query,
        catalog: dict[str, list[str]],
    ) -> list[QueryError]:
        table_names = {
            table_name.casefold(): table_name
            for table_name in catalog
        }
        fields_by_table = {
            table_name.casefold(): {
                field_name.casefold()
                for field_name in field_names
            }
            for table_name, field_names in catalog.items()
        }

        referenced_tables = [
            query.from_table,
            *[join.table for join in query.joins],
        ]
        query_tables = {
            table_name.casefold()
            for table_name in referenced_tables
        }

        errors: list[QueryError] = []

        for table_name in referenced_tables:
            if table_name.casefold() not in table_names:
                errors.append(
                    QueryError(
                        code="UNKNOWN_TABLE",
                        message=f'A tabela "{table_name}" não existe.',
                    )
                )

        for field in query.fields:
            errors.extend(
                self._validate_field(
                    field,
                    table_names,
                    fields_by_table,
                    query_tables,
                )
            )

        for join in query.joins:
            errors.extend(
                self._validate_expression(
                    join.condition,
                    table_names,
                    fields_by_table,
                    query_tables,
                )
            )

        if query.where is not None:
            errors.extend(
                self._validate_expression(
                    query.where,
                    table_names,
                    fields_by_table,
                    query_tables,
                )
            )

        unique_errors: list[QueryError] = []
        seen_errors: set[tuple[str, str]] = set()
        for error in errors:
            key = (error.code, error.message)
            if key not in seen_errors:
                seen_errors.add(key)
                unique_errors.append(error)

        return unique_errors
