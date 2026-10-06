"""Endpoints do caso de uso de análise de consultas."""

from fastapi import APIRouter

from backend.app.application.query_service import QueryService
from backend.app.infrastructure.schema_catalog import SCHEMA_CATALOG
from backend.app.schemas.query_schemas import (
    ApiError,
    ParseQueryRequest,
    ParseQueryResponse,
)

router = APIRouter(prefix="/queries", tags=["consultas"])
service = QueryService()


@router.post("/parse", response_model=ParseQueryResponse)
async def parse_query(payload: ParseQueryRequest) -> ParseQueryResponse:
    result = service.analyze(payload.sql)
    return ParseQueryResponse(
        valid=result.valid,
        tokens=[token.lexeme for token in result.tokens],
        query=None,
        errors=[
            ApiError(code=error.code, message=error.message, position=error.position)
            for error in result.errors
        ],
        graph=result.graph,
    )


@router.get("/schema")
async def get_schema() -> dict[str, list[str]]:
    return SCHEMA_CATALOG
