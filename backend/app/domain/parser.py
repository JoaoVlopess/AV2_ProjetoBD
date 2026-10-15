"""Análise sintática dos tokens e criação da AST."""

from backend.app.domain.ast_models import (
    AndExpression,
    Comparison,
    Expression,
    FieldReference,
    Join,
    Literal,
    Operand,
    Query,
)
from backend.app.domain.errors import QuerySyntaxError
from backend.app.domain.tokens import Token, TokenType


class Parser:
    def __init__(self):
        self.tokens: list[Token] = []
        self.current = 0

    def _advance(self) -> Token:
        token = self._current_token()

        if token.type != TokenType.EOF:
            self.current += 1

        return token

    def _current_token(self) -> Token:
        return self.tokens[self.current]

    def _expect_keyword(self, keyword: str) -> Token:
        token = self._current_token()

        if (
            token.type != TokenType.KEYWORD
            or token.lexeme.upper() != keyword
        ):
            raise QuerySyntaxError(
                message=f'Esperado "{keyword}", mas encontrado "{token.lexeme}".',
                position=token.position,
            )

        return self._advance()

    def _expect_type(
        self,
        expected_type: TokenType,
        message: str,
    ) -> Token:
        token = self._current_token()

        if token.type != expected_type:
            raise QuerySyntaxError(
                message=message,
                position=token.position,
            )

        return self._advance()

    def _check_type(self, token_type: TokenType) -> bool:
        return self._current_token().type == token_type

    def _check_keyword(self, keyword: str) -> bool:
        token = self._current_token()

        return (
            token.type == TokenType.KEYWORD
            and token.lexeme.upper() == keyword
        )

    def _parse_field(self) -> FieldReference:
        first_name = self._expect_type(
            TokenType.IDENTIFIER,
            "Esperado o nome de um campo.",
        )

        if self._check_type(TokenType.DOT):
            self._advance()
            field_name = self._expect_type(
                TokenType.IDENTIFIER,
                "Esperado o nome do campo depois do ponto.",
            )
            return FieldReference(
                name=field_name.lexeme,
                table=first_name.lexeme,
            )

        return FieldReference(name=first_name.lexeme)

    def _parse_field_list(self) -> list[FieldReference]:
        fields = [self._parse_field()]

        while self._check_type(TokenType.COMMA):
            self._advance()
            fields.append(self._parse_field())

        return fields

    def _parse_operand(self) -> Operand:
        token = self._current_token()

        if token.type == TokenType.IDENTIFIER:
            return self._parse_field()

        if token.type == TokenType.NUMBER:
            self._advance()
            value: int | float
            if "." in token.lexeme:
                value = float(token.lexeme)
            else:
                value = int(token.lexeme)
            return Literal(value=value)

        if token.type == TokenType.STRING:
            self._advance()
            return Literal(value=token.lexeme[1:-1])

        raise QuerySyntaxError(
            message="Esperado um campo, número ou texto na condição.",
            position=token.position,
        )

    def _parse_comparison(self) -> Comparison:
        left = self._parse_operand()
        operator = self._expect_type(
            TokenType.OPERATOR,
            "Esperado um operador de comparação.",
        )
        right = self._parse_operand()

        return Comparison(
            left=left,
            operator=operator.lexeme,
            right=right,
        )

    def _parse_condition(self) -> Expression:
        if self._check_type(TokenType.LEFT_PAREN):
            self._advance()
            expression = self._parse_expression()
            self._expect_type(
                TokenType.RIGHT_PAREN,
                "Esperado ')' para fechar a condição.",
            )
            return expression

        return self._parse_comparison()

    def _parse_expression(self) -> Expression:
        expression = self._parse_condition()

        while self._check_keyword("AND"):
            self._advance()
            right = self._parse_condition()
            expression = AndExpression(left=expression, right=right)

        return expression

    def _parse_join(self) -> Join:
        self._expect_keyword("INNER")
        self._expect_keyword("JOIN")
        table = self._expect_type(
            TokenType.IDENTIFIER,
            "Esperado o nome de uma tabela depois de INNER JOIN.",
        )
        self._expect_keyword("ON")
        condition = self._parse_expression()

        return Join(table=table.lexeme, condition=condition)

    def parse(self, tokens: list[Token]) -> Query:
        self.tokens = tokens
        self.current = 0

        self._expect_keyword("SELECT")
        fields = self._parse_field_list()
        self._expect_keyword("FROM")
        table_token = self._expect_type(
            TokenType.IDENTIFIER,
            "Esperado o nome de uma tabela depois de FROM.",
        )

        joins: list[Join] = []
        while self._check_keyword("INNER"):
            joins.append(self._parse_join())

        where: Expression | None = None
        if self._check_keyword("WHERE"):
            self._advance()
            where = self._parse_expression()

        if self._check_type(TokenType.SEMICOLON):
            self._advance()

        self._expect_type(
            TokenType.EOF,
            "Existem elementos depois do final da consulta.",
        )

        return Query(
            fields=fields,
            from_table=table_token.lexeme,
            joins=joins,
            where=where,
        )

