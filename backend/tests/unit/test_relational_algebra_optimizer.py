from backend.app.domain.ast_models import Comparison, FieldReference, Literal
from backend.app.domain.parser import Parser
from backend.app.domain.relational_algebra import (
    CartesianProduct,
    Projection,
    Relation,
    RelationalAlgebraConverter,
    Selection,
)
from backend.app.domain.relational_algebra_optimizer import (
    RelationalAlgebraOptimizer,
)
from backend.app.domain.tokenizer import Tokenizer
from backend.app.infrastructure.schema_catalog import SCHEMA_CATALOG


def optimize(sql: str):
    query = Parser().parse(Tokenizer().tokenize(sql))
    plan = RelationalAlgebraConverter().convert(query)
    return RelationalAlgebraOptimizer().optimize(plan, SCHEMA_CATALOG)


def test_pushes_each_selection_to_its_relation() -> None:
    plan = optimize(
        "SELECT Cliente.Nome, Pedido.idPedido FROM Cliente "
        "INNER JOIN Pedido "
        "ON Cliente.idCliente = Pedido.Cliente_idCliente "
        "WHERE Cliente.Email <> 'teste@email.com' "
        "AND Pedido.ValorTotalPedido >= 100;"
    )

    assert isinstance(plan, Projection)
    assert isinstance(plan.source, Selection)
    assert plan.source.clause == "ON"
    assert isinstance(plan.source.source, CartesianProduct)

    left = plan.source.source.left
    right = plan.source.source.right

    assert isinstance(left, Projection)
    assert isinstance(left.source, Selection)
    assert left.source.condition == Comparison(
        left=FieldReference(name="Email", table="Cliente"),
        operator="<>",
        right=Literal(value="teste@email.com"),
    )

    assert isinstance(right, Projection)
    assert isinstance(right.source, Selection)
    assert right.source.condition == Comparison(
        left=FieldReference(name="ValorTotalPedido", table="Pedido"),
        operator=">=",
        right=Literal(value=100),
    )


def test_early_projections_keep_only_required_fields() -> None:
    plan = optimize(
        "SELECT Cliente.Nome, Pedido.idPedido FROM Cliente "
        "INNER JOIN Pedido "
        "ON Cliente.idCliente = Pedido.Cliente_idCliente "
        "WHERE Cliente.Email <> 'teste@email.com' "
        "AND Pedido.ValorTotalPedido >= 100;"
    )

    assert isinstance(plan, Projection)
    assert isinstance(plan.source, Selection)
    assert isinstance(plan.source.source, CartesianProduct)
    assert isinstance(plan.source.source.left, Projection)
    assert isinstance(plan.source.source.right, Projection)

    assert plan.source.source.left.fields == [
        FieldReference(name="idCliente", table="Cliente"),
        FieldReference(name="Nome", table="Cliente"),
    ]
    assert plan.source.source.right.fields == [
        FieldReference(name="idPedido", table="Pedido"),
        FieldReference(name="Cliente_idCliente", table="Pedido"),
    ]


def test_does_not_push_condition_between_tables_into_one_relation() -> None:
    plan = optimize(
        "SELECT Cliente.Nome FROM Cliente "
        "INNER JOIN Pedido "
        "ON Cliente.idCliente = Pedido.Cliente_idCliente "
        "WHERE Cliente.idCliente = Pedido.Cliente_idCliente;"
    )

    assert isinstance(plan, Projection)
    assert isinstance(plan.source, Selection)
    assert plan.source.clause == "ON"
    assert isinstance(plan.source.source, Selection)
    assert plan.source.source.clause == "WHERE"
    assert isinstance(plan.source.source.source, CartesianProduct)


def test_single_table_plan_does_not_add_redundant_projection() -> None:
    plan = optimize(
        "SELECT Nome FROM Cliente WHERE idCliente >= 10;"
    )

    assert plan == Projection(
        source=Selection(
            source=Relation(table="Cliente"),
            condition=Comparison(
                left=FieldReference(name="idCliente"),
                operator=">=",
                right=Literal(value=10),
            ),
        ),
        fields=[FieldReference(name="Nome")],
    )
