"""Endpoints do caso de uso de análise de consultas."""

from dataclasses import asdict

from fastapi import APIRouter

from backend.app.application.query_service import QueryService
from backend.app.domain.ast_models import FieldReference, Query
from backend.app.domain.tokens import TokenType
from backend.app.infrastructure.schema_catalog import SCHEMA_CATALOG
from backend.app.schemas.query_schemas import (
    ApiError,
    ParseQueryRequest,
    ParseQueryResponse,
    ParsedQuery,
)

router = APIRouter(prefix="/queries", tags=["consultas"])
service = QueryService()


def _format_field(field: FieldReference) -> str:
    if field.table is not None:
        return f"{field.table}.{field.name}"
    return field.name


def _serialize_query(query: Query | None) -> ParsedQuery | None:
    if query is None:
        return None

    return ParsedQuery(
        select_fields=[_format_field(field) for field in query.fields],
        from_table=query.from_table,
        joins=[asdict(join) for join in query.joins],
        where=asdict(query.where) if query.where is not None else None,
    )


@router.post("/parse", response_model=ParseQueryResponse)
async def parse_query(payload: ParseQueryRequest) -> ParseQueryResponse:
    result = service.analyze(payload.sql)
    return ParseQueryResponse(
        valid=result.valid,
        tokens=[
            token.lexeme
            for token in result.tokens
            if token.type != TokenType.EOF
        ],
        query=_serialize_query(result.query),
        errors=[
            ApiError(code=error.code, message=error.message, position=error.position)
            for error in result.errors
        ],
        graph=result.graph,
    )


@router.get("/schema")
async def get_schema() -> dict[str, list[str]]:
    return SCHEMA_CATALOG
