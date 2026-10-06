"""Conversão futura da AST em um grafo direcionado NetworkX."""

import networkx as nx

from backend.app.domain.ast_models import Query


class GraphBuilder:
    def build(self, query: Query) -> nx.DiGraph:
        raise NotImplementedError("O grafo pertence às próximas entregas.")
