"""Atalho para iniciar o monólito a partir da raiz do projeto."""

import uvicorn


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
