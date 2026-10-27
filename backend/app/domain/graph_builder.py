"""Construção do grafo do plano de álgebra relacional."""

from itertools import count
from collections.abc import Mapping
from typing import Iterator

import networkx as nx

from backend.app.domain.relational_algebra import (
    CartesianProduct,
    Projection,
    Relation,
    RelationalAlgebraFormatter,
    RelationalNode,
    Selection,
)


class GraphBuilder:
    """Transforma a árvore relacional em um grafo dirigido NetworkX."""

    def build(
        self,
        plan: RelationalNode,
        table_cardinalities: Mapping[str, int] | None = None,
    ) -> nx.DiGraph:
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
            table_cardinalities or {},
        )
        graph.graph["root"] = root_id
        graph.nodes[root_id]["is_root"] = True
        return graph

    def _add_node(
        self,
        graph: nx.DiGraph,
        node: RelationalNode,
        node_ids: Iterator[int],
        edge_ids: Iterator[int],
        formatter: RelationalAlgebraFormatter,
        table_cardinalities: Mapping[str, int],
    ) -> str:
        node_id = f"n{next(node_ids)}"

        if isinstance(node, Relation):
            cardinality = table_cardinalities.get(node.table)
            label = node.table
            detail = "Tabela"
            if cardinality is not None:
                label = f"{node.table}\n{cardinality:,} tuplas".replace(",", ".")
                detail = f"Tabela com {cardinality:,} tuplas".replace(",", ".")

            graph.add_node(
                node_id,
                kind="relation",
                label=label,
                detail=detail,
                cardinality=cardinality,
            )
            return node_id

        if isinstance(node, CartesianProduct):
            graph.add_node(
                node_id,
                kind="product",
                label="×",
                detail="Produto cartesiano",
            )
            left_id = self._add_node(
                graph,
                node.left,
                node_ids,
                edge_ids,
                formatter,
                table_cardinalities,
            )
            right_id = self._add_node(
                graph,
                node.right,
                node_ids,
                edge_ids,
                formatter,
                table_cardinalities,
            )
            self._add_edge(graph, left_id, node_id, edge_ids)
            self._add_edge(graph, right_id, node_id, edge_ids)
            return node_id

        if isinstance(node, Selection):
            condition = formatter.format_expression(node.condition)
            graph.add_node(
                node_id,
                kind="selection",
                label=f"σ {node.clause}\n{condition}",
                clause=node.clause,
                detail=condition,
            )
            source_id = self._add_node(
                graph,
                node.source,
                node_ids,
                edge_ids,
                formatter,
                table_cardinalities,
            )
            self._add_edge(graph, source_id, node_id, edge_ids)
            return node_id

        fields = ", ".join(
            formatter.format_field(field) for field in node.fields
        )
        graph.add_node(
            node_id,
            kind="projection",
            label=f"π PROJEÇÃO (SELECT)\n{fields}",
            detail=fields,
        )
        source_id = self._add_node(
            graph,
            node.source,
            node_ids,
            edge_ids,
            formatter,
            table_cardinalities,
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
