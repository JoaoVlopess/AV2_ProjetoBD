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

    branches = [plan.source.source.left, plan.source.source.right]
    left = next(
        branch
        for branch in branches
        if optimizer_relation_names(branch) == {"Cliente"}
    )
    right = next(
        branch
        for branch in branches
        if optimizer_relation_names(branch) == {"Pedido"}
    )

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
    branches = [plan.source.source.left, plan.source.source.right]
    cliente = next(
        branch
        for branch in branches
        if optimizer_relation_names(branch) == {"Cliente"}
    )
    pedido = next(
        branch
        for branch in branches
        if optimizer_relation_names(branch) == {"Pedido"}
    )
    assert isinstance(cliente, Projection)
    assert isinstance(pedido, Projection)

    assert cliente.fields == [
        FieldReference(name="idCliente", table="Cliente"),
        FieldReference(name="Nome", table="Cliente"),
    ]
    assert pedido.fields == [
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


def test_applies_most_restrictive_selection_first() -> None:
    plan = optimize(
        "SELECT Nome FROM Cliente "
        "WHERE idCliente <> 1 AND Nome = 'Ana';"
    )

    assert isinstance(plan, Projection)
    assert isinstance(plan.source, Selection)
    assert plan.source.condition.operator == "<>"
    assert isinstance(plan.source.source, Selection)
    assert plan.source.source.condition.operator == "="


def test_reorders_leaves_and_uses_most_restrictive_join_first() -> None:
    plan = optimize(
        "SELECT Cliente.Nome, Pedido.idPedido, Status.Descricao "
        "FROM Cliente "
        "INNER JOIN Pedido "
        "ON Cliente.idCliente > Pedido.Cliente_idCliente "
        "INNER JOIN Status "
        "ON Pedido.Status_idStatus = Status.idStatus "
        "WHERE Pedido.ValorTotalPedido = 100;"
    )

    assert isinstance(plan, Projection)
    assert isinstance(plan.source, Selection)
    assert plan.source.condition.operator == ">"
    assert isinstance(plan.source.source, CartesianProduct)
    assert isinstance(plan.source.source.left, Selection)
    assert plan.source.source.left.condition.operator == "="
    assert {
        *optimizer_relation_names(plan.source.source.left.source.left),
        *optimizer_relation_names(plan.source.source.left.source.right),
    } == {"Pedido", "Status"}


def test_every_product_in_optimized_plan_has_an_on_selection() -> None:
    plan = optimize(
        "SELECT Cliente.Nome, Pedido.idPedido FROM Cliente "
        "INNER JOIN Pedido "
        "ON Cliente.idCliente = Pedido.Cliente_idCliente;"
    )

    assert not contains_unfiltered_product(plan)


def optimizer_relation_names(node) -> set[str]:
    if isinstance(node, Relation):
        return {node.table}
    if isinstance(node, CartesianProduct):
        return optimizer_relation_names(node.left) | optimizer_relation_names(
            node.right
        )
    return optimizer_relation_names(node.source)


def contains_unfiltered_product(node, parent_is_on: bool = False) -> bool:
    if isinstance(node, CartesianProduct):
        return (
            not parent_is_on
            or contains_unfiltered_product(node.left)
            or contains_unfiltered_product(node.right)
        )
    if isinstance(node, Relation):
        return False
    if isinstance(node, Selection):
        return contains_unfiltered_product(
            node.source,
            parent_is_on=node.clause == "ON",
        )
    return contains_unfiltered_product(node.source)
