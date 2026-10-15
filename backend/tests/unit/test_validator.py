import pytest

from backend.app.domain.parser import Parser
from backend.app.domain.tokenizer import Tokenizer
from backend.app.domain.validator import QueryValidator
from backend.app.infrastructure.schema_catalog import SCHEMA_CATALOG


def validate(sql: str):
    query = Parser().parse(Tokenizer().tokenize(sql))
    return QueryValidator().validate(query, SCHEMA_CATALOG)


def test_accepts_existing_tables_and_fields() -> None:
    errors = validate(
        "SELECT Cliente.Nome, Pedido.idPedido FROM Cliente "
        "INNER JOIN Pedido "
        "ON Cliente.idCliente = Pedido.Cliente_idCliente "
        "WHERE Pedido.ValorTotalPedido >= 500;"
    )

    assert errors == []


def test_validation_is_case_insensitive() -> None:
    assert validate("SELECT nome FROM cliente;") == []


@pytest.mark.parametrize(
    ("sql", "error_code"),
    [
        ("SELECT Nome FROM Clientes;", "UNKNOWN_TABLE"),
        ("SELECT Telefone FROM Cliente;", "UNKNOWN_FIELD"),
        ("SELECT Cliente.Preco FROM Cliente;", "UNKNOWN_FIELD"),
        ("SELECT Produto.Nome FROM Cliente;", "TABLE_NOT_IN_QUERY"),
        (
            "SELECT Descricao FROM Produto "
            "INNER JOIN Categoria "
            "ON Produto.Categoria_idCategoria = Categoria.idCategoria;",
            "AMBIGUOUS_FIELD",
        ),
        (
            "SELECT Cliente.Nome FROM Cliente "
            "WHERE Cliente.CampoInexistente = 1;",
            "UNKNOWN_FIELD",
        ),
    ],
)
def test_rejects_invalid_tables_and_fields(sql: str, error_code: str) -> None:
    errors = validate(sql)

    assert error_code in [error.code for error in errors]
