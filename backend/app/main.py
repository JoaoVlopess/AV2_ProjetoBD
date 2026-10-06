"""Ponto de entrada HTTP e hospedagem do frontend compilado."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from backend.app.api.routes import api_router

APP_DIR = Path(__file__).resolve().parent
STATIC_ROOT = APP_DIR / "static"
ANGULAR_ROOT = STATIC_ROOT / "dist" / "browser"
if not (ANGULAR_ROOT / "index.html").exists():
    ANGULAR_ROOT = STATIC_ROOT / "browser"
if not (ANGULAR_ROOT / "index.html").exists():
    ANGULAR_ROOT = STATIC_ROOT

app = FastAPI(
    title="Processador de Consultas",
    version="0.1.0",
    description="Parser, validador e processador de consultas acadêmico.",
)
app.include_router(api_router, prefix="/api/v1")


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_angular(full_path: str):
    """Serve arquivos do Angular e aplica fallback para a SPA."""
    index_file = ANGULAR_ROOT / "index.html"
    if not index_file.exists():
        return JSONResponse(
            {
                "message": "Frontend ainda não compilado.",
                "next_step": "Execute scripts/build.ps1 ou use o Angular em localhost:4200.",
            }
        )

    requested_file = (ANGULAR_ROOT / full_path).resolve()
    try:
        requested_file.relative_to(ANGULAR_ROOT.resolve())
    except ValueError:
        return FileResponse(index_file)

    if requested_file.is_file():
        return FileResponse(requested_file)
    return FileResponse(index_file)
