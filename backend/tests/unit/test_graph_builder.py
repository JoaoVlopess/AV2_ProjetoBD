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


def test_join_receives_both_relations() -> None:
    graph = build_graph(
        "SELECT Cliente.Nome, Pedido.idPedido FROM Cliente "
        "INNER JOIN Pedido "
        "ON Cliente.idCliente = Pedido.Cliente_idCliente;"
    )

    join_id = next(
        node_id
        for node_id, data in graph.nodes(data=True)
        if data["kind"] == "join"
    )
    input_kinds = {
        graph.nodes[node_id]["kind"] for node_id in graph.predecessors(join_id)
    }

    assert input_kinds == {"relation"}
    assert len(list(graph.predecessors(join_id))) == 2


def test_projection_is_the_graph_root() -> None:
    graph = build_graph("SELECT Nome FROM Cliente;")
    root_id = graph.graph["root"]

    assert graph.nodes[root_id]["kind"] == "projection"
    assert graph.out_degree(root_id) == 0
