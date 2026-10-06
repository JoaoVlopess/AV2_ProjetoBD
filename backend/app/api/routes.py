"""Agregação das rotas da API v1."""

from fastapi import APIRouter

from backend.app.api.query_routes import router as query_router

api_router = APIRouter()
api_router.include_router(query_router)


@api_router.get("/health", tags=["infraestrutura"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
