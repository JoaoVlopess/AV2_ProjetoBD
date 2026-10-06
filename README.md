# Processador de Consultas

Monólito modular para analisar um subconjunto de SQL, validar tabelas e campos e, nas próximas etapas, construir e visualizar o grafo de operadores.

## Tecnologias

- Angular 22 e TypeScript no frontend;
- FastAPI, Pydantic e Python 3.13 no backend;
- NetworkX para construir e processar o grafo;
- Cytoscape.js para renderizar o grafo no navegador.

## Estrutura

```text
frontend/            interface Angular
backend/app/api/     endpoints HTTP
backend/app/application/ casos de uso
backend/app/domain/  parser, validação e grafo
backend/app/infrastructure/ catálogo BD_Vendas
scripts/             comandos de configuração, build e execução
```

Consulte [MAPEAMENTO_PRIMEIRA_ENTREGA.md](MAPEAMENTO_PRIMEIRA_ENTREGA.md) para requisitos, decisões arquiteturais e casos de teste.

## Preparação

No PowerShell, a partir da raiz:

```powershell
.\scripts\setup.ps1
```

## Desenvolvimento

Use dois terminais:

```powershell
.\scripts\run-backend.ps1
```

```powershell
.\scripts\run-frontend.ps1
```

A interface estará em `http://localhost:4200`, a API em `http://localhost:8000` e o Swagger em `http://localhost:8000/docs`.

## Build monolítico

```powershell
.\scripts\build.ps1
.\scripts\run.ps1
```

Depois do build, o FastAPI serve tanto `/api/*` quanto a aplicação Angular em `http://localhost:8000`.

## Testes

```powershell
.\venv\Scripts\python.exe -m pytest backend\tests
Set-Location frontend
npm test
```

O endpoint do parser está criado, mas retorna `NOT_IMPLEMENTED` até a implementação do tokenizador, parser e validador.
