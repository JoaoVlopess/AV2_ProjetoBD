"""Construção do grafo do plano de álgebra relacional."""

from itertools import count
from typing import Iterator

import networkx as nx

from backend.app.domain.relational_algebra import (
    JoinOperation,
    Projection,
    Relation,
    RelationalAlgebraFormatter,
    RelationalNode,
    Selection,
)


class GraphBuilder:
    """Transforma a árvore relacional em um grafo dirigido NetworkX."""

    def build(self, plan: RelationalNode) -> nx.DiGraph:
        graph = nx.DiGraph()
        node_ids = count(1)
        edge_ids = count(1)
        formatter = RelationalAlgebraFormatter()

        root_id = self._add_node(
            graph,
            plan,
            node_ids,
            edge_ids,
            formatter,
        )
        graph.graph["root"] = root_id
        return graph

    def _add_node(
        self,
        graph: nx.DiGraph,
        node: RelationalNode,
        node_ids: Iterator[int],
        edge_ids: Iterator[int],
        formatter: RelationalAlgebraFormatter,
    ) -> str:
        node_id = f"n{next(node_ids)}"

        if isinstance(node, Relation):
            graph.add_node(
                node_id,
                kind="relation",
                label=node.table,
                detail="Tabela",
            )
            return node_id

        if isinstance(node, JoinOperation):
            condition = formatter.format_expression(node.condition)
            graph.add_node(
                node_id,
                kind="join",
                label=f"⋈ JOIN\n{condition}",
                detail=condition,
            )
            left_id = self._add_node(
                graph, node.left, node_ids, edge_ids, formatter
            )
            right_id = self._add_node(
                graph, node.right, node_ids, edge_ids, formatter
            )
            self._add_edge(graph, left_id, node_id, edge_ids)
            self._add_edge(graph, right_id, node_id, edge_ids)
            return node_id

        if isinstance(node, Selection):
            condition = formatter.format_expression(node.condition)
            graph.add_node(
                node_id,
                kind="selection",
                label=f"σ WHERE\n{condition}",
                detail=condition,
            )
            source_id = self._add_node(
                graph, node.source, node_ids, edge_ids, formatter
            )
            self._add_edge(graph, source_id, node_id, edge_ids)
            return node_id

        fields = ", ".join(
            formatter.format_field(field) for field in node.fields
        )
        graph.add_node(
            node_id,
            kind="projection",
            label=f"π SELECT\n{fields}",
            detail=fields,
        )
        source_id = self._add_node(
            graph, node.source, node_ids, edge_ids, formatter
        )
        self._add_edge(graph, source_id, node_id, edge_ids)
        return node_id

    @staticmethod
    def _add_edge(
        graph: nx.DiGraph,
        source: str,
        target: str,
        edge_ids: Iterator[int],
    ) -> None:
        graph.add_edge(
            source,
            target,
            id=f"e{next(edge_ids)}",
        )
