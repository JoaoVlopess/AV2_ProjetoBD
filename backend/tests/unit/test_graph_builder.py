import networkx as nx

from backend.app.domain.graph_builder import GraphBuilder
from backend.app.domain.parser import Parser
from backend.app.domain.relational_algebra import RelationalAlgebraConverter
from backend.app.domain.tokenizer import Tokenizer


def build_graph(sql: str) -> nx.DiGraph:
    query = Parser().parse(Tokenizer().tokenize(sql))
    plan = RelationalAlgebraConverter().convert(query)
    return GraphBuilder().build(plan)


def test_builds_directed_graph_for_select_and_where() -> None:
    graph = build_graph(
        "SELECT Nome FROM Cliente WHERE idCliente >= 10;"
    )

    kinds = {data["kind"] for _, data in graph.nodes(data=True)}

    assert graph.is_directed()
    assert nx.is_directed_acyclic_graph(graph)
    assert kinds == {"relation", "selection", "projection"}
    assert graph.number_of_nodes() == 3
    assert graph.number_of_edges() == 2


def test_product_receives_both_relations_below_on_selection() -> None:
    graph = build_graph(
        "SELECT Cliente.Nome, Pedido.idPedido FROM Cliente "
        "INNER JOIN Pedido "
        "ON Cliente.idCliente = Pedido.Cliente_idCliente;"
    )

    product_id = next(
        node_id
        for node_id, data in graph.nodes(data=True)
        if data["kind"] == "product"
    )
    input_kinds = {
        graph.nodes[node_id]["kind"] for node_id in graph.predecessors(product_id)
    }

    assert input_kinds == {"relation"}
    assert len(list(graph.predecessors(product_id))) == 2


def test_projection_is_the_graph_root() -> None:
    graph = build_graph("SELECT Nome FROM Cliente;")
    root_id = graph.graph["root"]

    assert graph.nodes[root_id]["kind"] == "projection"
    assert graph.out_degree(root_id) == 0


def test_two_joins_and_where_preserve_the_primitive_tree() -> None:
    graph = build_graph(
        "SELECT Cliente.Nome FROM Cliente "
        "INNER JOIN Pedido ON Cliente.idCliente = Pedido.Cliente_idCliente "
        "INNER JOIN Status ON Pedido.Status_idStatus = Status.idStatus "
        "WHERE Pedido.ValorTotalPedido >= 100;"
    )
    assert nx.is_tree(graph.to_undirected())
    assert nx.is_directed_acyclic_graph(graph)
    assert all(data["kind"] in {"relation", "product", "selection", "projection"}
               for _, data in graph.nodes(data=True))
    assert sum(data["kind"] == "product" for _, data in graph.nodes(data=True)) == 2

    def input_of(node):
        inputs = list(graph.predecessors(node))
        assert len(inputs) == 1
        return inputs[0]

    root = graph.graph["root"]
    assert graph.nodes[root]["kind"] == "projection"
    where = input_of(root)
    assert graph.nodes[where]["clause"] == "WHERE"
    second_on = input_of(where)
    assert graph.nodes[second_on]["label"] == "σ ON\nPedido.Status_idStatus = Status.idStatus"
    second_product = input_of(second_on)
    assert graph.nodes[second_product]["kind"] == "product"
    inputs = list(graph.predecessors(second_product))
    assert len(inputs) == 2
    first_on = next(node for node in inputs if graph.nodes[node]["kind"] == "selection")
    assert {graph.nodes[node]["label"] for node in inputs if node != first_on} == {"Status"}
    assert graph.nodes[first_on]["label"] == "σ ON\nCliente.idCliente = Pedido.Cliente_idCliente"
    first_product = input_of(first_on)
    assert graph.nodes[first_product]["kind"] == "product"
    assert {graph.nodes[node]["label"] for node in graph.predecessors(first_product)} == {"Cliente", "Pedido"}
