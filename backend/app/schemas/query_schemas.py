"""Modelos Pydantic do endpoint de análise."""

from typing import Any

from pydantic import BaseModel, Field


class ParseQueryRequest(BaseModel):
    sql: str = Field(min_length=1, description="Consulta SQL a analisar.")


class ApiError(BaseModel):
    code: str
    message: str
    position: int | None = None


class ParsedQuery(BaseModel):
    select_fields: list[str] = Field(serialization_alias="select")
    from_table: str = Field(serialization_alias="from")
    joins: list[dict[str, Any]] = Field(default_factory=list)
    where: dict[str, Any] | None = None


class ParseQueryResponse(BaseModel):
    valid: bool
    tokens: list[str] = Field(default_factory=list)
    query: ParsedQuery | None = None
    errors: list[ApiError] = Field(default_factory=list)
    algebra: str | None = None
    graph: dict[str, Any] | None = None
    optimized_algebra: str | None = None
    optimized_graph: dict[str, Any] | None = None
