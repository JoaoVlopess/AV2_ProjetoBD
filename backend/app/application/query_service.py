"""Orquestra tokenização, parsing, validação e construção do grafo."""

from backend.app.domain.errors import QueryError
from backend.app.domain.models import QueryAnalysisResult


class QueryService:
    """Fachada do caso de uso de análise de uma consulta SQL."""

    def analyze(self, sql: str) -> QueryAnalysisResult:
        # A estrutura está pronta; a implementação pertence à próxima tarefa.
        return QueryAnalysisResult(
            valid=False,
            tokens=[],
            query=None,
            errors=[
                QueryError(
                    code="NOT_IMPLEMENTED",
                    message="Tokenizador, parser e validador ainda serão implementados.",
                )
            ],
            graph=None,
        )
