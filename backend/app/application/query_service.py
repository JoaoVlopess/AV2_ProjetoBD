"""Orquestra tokenização, parsing, validação e construção do grafo."""

from networkx.readwrite import json_graph

from backend.app.domain.errors import (
    QueryError,
    QueryLexicalError,
    QuerySyntaxError,
)
from backend.app.domain.graph_builder import GraphBuilder
from backend.app.domain.models import QueryAnalysisResult
from backend.app.domain.parser import Parser
from backend.app.domain.relational_algebra import (
    RelationalAlgebraConverter,
    RelationalAlgebraFormatter,
)
from backend.app.domain.relational_algebra_optimizer import (
    RelationalAlgebraOptimizer,
)
from backend.app.domain.tokenizer import Tokenizer
from backend.app.domain.validator import QueryValidator
from backend.app.infrastructure.schema_catalog import SCHEMA_CATALOG


class QueryService:
    """Fachada do caso de uso de análise de uma consulta SQL."""

    def analyze(self, sql: str) -> QueryAnalysisResult:
        try:
            tokens = Tokenizer().tokenize(sql)
            query = Parser().parse(tokens)
        except QueryLexicalError as error:
            return QueryAnalysisResult(
                valid=False,
                errors=[
                    QueryError(
                        code="LEXICAL_ERROR",
                        message=error.message,
                        position=error.position,
                    )
                ],
            )
        except QuerySyntaxError as error:
            return QueryAnalysisResult(
                valid=False,
                tokens=tokens,
                errors=[
                    QueryError(
                        code="SYNTAX_ERROR",
                        message=error.message,
                        position=error.position,
                    )
                ],
            )

        errors = QueryValidator().validate(query, SCHEMA_CATALOG)

        algebra = None
        graph_data = None
        optimized_algebra = None
        optimized_graph_data = None
        if not errors:
            plan = RelationalAlgebraConverter().convert(query)
            formatter = RelationalAlgebraFormatter()
            algebra = formatter.format(plan)
            graph = GraphBuilder().build(plan)
            graph_data = json_graph.cytoscape_data(graph)

            optimized_plan = RelationalAlgebraOptimizer().optimize(
                plan,
                SCHEMA_CATALOG,
            )
            optimized_algebra = formatter.format(optimized_plan)
            optimized_graph = GraphBuilder().build(optimized_plan)
            optimized_graph_data = json_graph.cytoscape_data(optimized_graph)

        return QueryAnalysisResult(
            valid=not errors,
            tokens=tokens,
            query=query,
            errors=errors,
            algebra=algebra,
            graph=graph_data,
            optimized_algebra=optimized_algebra,
            optimized_graph=optimized_graph_data,
        )
