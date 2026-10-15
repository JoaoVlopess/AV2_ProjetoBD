import re

import pytest

from backend.app.domain.ast_models import AndExpression, Comparison, FieldReference, Literal
from backend.app.domain.parser import Parser, QuerySyntaxError
from backend.app.domain.tokenizer import Tokenizer


def parse(sql: str):
    return Parser().parse(Tokenizer().tokenize(sql))


def test_parses_simple_select() -> None:
    query = parse("SELECT Nome FROM Cliente;")

    assert query.fields == [FieldReference(name="Nome")]
    assert query.from_table == "Cliente"
    assert query.joins == []
    assert query.where is None


def test_parses_multiple_and_qualified_fields() -> None:
    query = parse("SELECT Cliente.Nome, Cliente.Email FROM Cliente")

    assert query.fields == [
        FieldReference(name="Nome", table="Cliente"),
        FieldReference(name="Email", table="Cliente"),
    ]


def test_parses_where_with_and_and_parentheses() -> None:
    query = parse(
        "SELECT Nome FROM Cliente "
        "WHERE (idCliente >= 10 AND Nome = 'Ana Maria');"
    )

    assert query.where == AndExpression(
        left=Comparison(
            left=FieldReference(name="idCliente"),
            operator=">=",
            right=Literal(value=10),
        ),
        right=Comparison(
            left=FieldReference(name="Nome"),
            operator="=",
            right=Literal(value="Ana Maria"),
        ),
    )


def test_parses_inner_join() -> None:
    query = parse(
        "SELECT Cliente.Nome, Pedido.idPedido FROM Cliente "
        "INNER JOIN Pedido "
        "ON Cliente.idCliente = Pedido.Cliente_idCliente;"
    )

    assert query.joins[0].table == "Pedido"
    assert query.joins[0].condition == Comparison(
        left=FieldReference(name="idCliente", table="Cliente"),
        operator="=",
        right=FieldReference(name="Cliente_idCliente", table="Pedido"),
    )


@pytest.mark.parametrize(
    ("sql", "message"),
    [
        ("UPDATE Cliente;", 'Esperado "SELECT"'),
        ("SELECT FROM Cliente;", "Esperado o nome de um campo"),
        ("SELECT Nome Cliente;", 'Esperado "FROM"'),
        ("SELECT Nome FROM Cliente WHERE idCliente >;", "Esperado um campo"),
        ("SELECT Nome FROM Cliente WHERE (idCliente > 1;", "Esperado ')'"),
        ("SELECT Nome FROM Cliente algo;", "Existem elementos"),
    ],
)
def test_reports_syntax_errors(sql: str, message: str) -> None:
    with pytest.raises(QuerySyntaxError, match=re.escape(message)):
        parse(sql)
