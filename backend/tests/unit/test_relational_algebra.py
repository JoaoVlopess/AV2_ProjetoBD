from backend.app.domain.ast_models import Comparison, FieldReference, Literal
from backend.app.domain.parser import Parser
from backend.app.domain.relational_algebra import (
    JoinOperation,
    Projection,
    Relation,
    RelationalAlgebraConverter,
    RelationalAlgebraFormatter,
    Selection,
)
from backend.app.domain.tokenizer import Tokenizer


def convert(sql: str):
    query = Parser().parse(Tokenizer().tokenize(sql))
    return RelationalAlgebraConverter().convert(query)


def test_converts_simple_select() -> None:
    plan = convert("SELECT Nome FROM Cliente;")

    assert plan == Projection(
        source=Relation(table="Cliente"),
        fields=[FieldReference(name="Nome")],
    )


def test_converts_where_without_optimizing_it() -> None:
    plan = convert("SELECT Nome FROM Cliente WHERE idCliente >= 10;")

    assert isinstance(plan, Projection)
    assert plan.source == Selection(
        source=Relation(table="Cliente"),
        condition=Comparison(
            left=FieldReference(name="idCliente"),
            operator=">=",
            right=Literal(value=10),
        ),
    )


def test_converts_join_and_where_in_sql_order() -> None:
    plan = convert(
        "SELECT Cliente.Nome, Pedido.idPedido FROM Cliente "
        "INNER JOIN Pedido "
        "ON Cliente.idCliente = Pedido.Cliente_idCliente "
        "WHERE Pedido.ValorTotalPedido >= 500;"
    )

    assert isinstance(plan, Projection)
    assert isinstance(plan.source, Selection)
    assert isinstance(plan.source.source, JoinOperation)
    assert plan.source.source.left == Relation(table="Cliente")
    assert plan.source.source.right == Relation(table="Pedido")


def test_formats_relational_algebra() -> None:
    plan = convert("SELECT Nome FROM Cliente WHERE idCliente >= 10;")

    assert RelationalAlgebraFormatter().format(plan) == (
        "π[Nome](σ[idCliente >= 10](Cliente))"
    )
