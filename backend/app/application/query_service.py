"""Orquestra tokenização, parsing, validação e construção do grafo."""

from backend.app.domain.errors import (
    QueryError,
    QueryLexicalError,
    QuerySyntaxError,
)
from backend.app.domain.models import QueryAnalysisResult
from backend.app.domain.parser import Parser
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

        return QueryAnalysisResult(
            valid=not errors,
            tokens=tokens,
            query=query,
            errors=errors,
            graph=None,
        )
