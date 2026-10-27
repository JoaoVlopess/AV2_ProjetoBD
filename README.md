# Processador de Consultas SQL

Projeto acadêmico que analisa um subconjunto da linguagem SQL e apresenta a consulta como uma árvore de álgebra relacional, antes e depois da aplicação de heurísticas de otimização.

A aplicação possui uma interface Angular e um backend FastAPI. O backend faz a análise da consulta e usa NetworkX para gerar os grafos; o frontend usa Cytoscape.js para exibi-los.

## O que o projeto faz

Ao enviar uma consulta SQL, a aplicação executa este fluxo:

```text
SQL
  → análise léxica (tokenizer)
  → análise sintática (parser)
  → construção da AST
  → validação de tabelas e campos
  → álgebra relacional não otimizada
  → aplicação das heurísticas
  → álgebra relacional otimizada
  → geração e exibição dos grafos
```

O projeto reconhece:

- `SELECT`, `FROM`, `WHERE`, `INNER JOIN`, `ON` e `AND`;
- campos simples e qualificados, como `Nome` e `Cliente.Nome`;
- números e textos entre aspas simples;
- operadores `=`, `>`, `<`, `<=`, `>=` e `<>`;
- múltiplas junções e condições entre parênteses.

O processador valida erros léxicos, sintáticos e semânticos, incluindo tabelas e campos inexistentes.

> Este é um processador acadêmico de consultas. Ele analisa e otimiza o plano lógico, mas não executa a consulta em um banco de dados real.

## Álgebra relacional e otimização

O plano utiliza somente os elementos primitivos necessários ao subconjunto implementado:

- relação (tabela);
- seleção `σ`;
- projeção `π`;
- produto cartesiano `×`.

Um `INNER JOIN` é representado sem criar um operador de junção próprio:

```text
R JOIN S ON condição  =  σ condição (R × S)
```

O otimizador aplica as seguintes heurísticas:

- leva as seleções para perto das tabelas correspondentes;
- executa primeiro as seleções estimadas como mais restritivas;
- insere projeções antecipadas para remover colunas desnecessárias;
- começa pelas relações que possuem filtros mais restritivos;
- reorganiza as junções para aplicar primeiro as condições mais restritivas;
- evita produtos cartesianos sem uma seleção `ON` associada quando existe uma condição de junção.

## Tecnologias

- Python 3.13;
- FastAPI e Pydantic;
- NetworkX;
- Angular 22 e TypeScript;
- Cytoscape.js;
- Pytest e Vitest.

## Pré-requisitos

Instale:

- Python 3.13 ou compatível;
- Node.js 24.15 ou superior;
- npm 11 ou superior.

Os comandos abaixo foram preparados para PowerShell no Windows.

## Instalação

Abra o PowerShell na raiz do projeto e crie o ambiente virtual:

```powershell
python -m venv venv
```

Depois instale as dependências do backend e do frontend:

```powershell
.\scripts\setup.ps1
```

Se o PowerShell bloquear os scripts, libere a execução apenas para o terminal atual e tente novamente:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

## Como rodar em desenvolvimento

Use dois terminais abertos na raiz do projeto.

No primeiro terminal, inicie o backend:

```powershell
.\scripts\run-backend.ps1
```

No segundo terminal, inicie o frontend:

```powershell
.\scripts\run-frontend.ps1
```

Acesse:

- interface: http://localhost:4200
- API: http://127.0.0.1:8000
- documentação Swagger: http://127.0.0.1:8000/docs
- verificação do backend: http://127.0.0.1:8000/api/v1/health

O servidor Angular encaminha automaticamente as chamadas `/api` para o backend pela configuração de proxy do projeto.

### Execução manual

Se preferir não usar os scripts, execute o backend na raiz:

```powershell
.\venv\Scripts\python.exe main.py
```

Em outro terminal, execute o frontend:

```powershell
cd frontend
npm start
```

## Como rodar como monólito compilado

O build do Angular é gravado dentro da pasta estática do backend. Assim, depois da compilação, o FastAPI serve a API e a interface pela mesma porta.

Na raiz do projeto, execute:

```powershell
.\scripts\build.ps1
.\scripts\run.ps1
```

Depois acesse:

```text
http://127.0.0.1:8000
```

## Consulta para teste

```sql
SELECT Cliente.Nome, Pedido.idPedido, Status.Descricao
FROM Cliente
INNER JOIN Pedido
    ON Cliente.idCliente = Pedido.Cliente_idCliente
INNER JOIN Status
    ON Pedido.Status_idStatus = Status.idStatus
WHERE Pedido.ValorTotalPedido >= 100;
```

A interface deverá mostrar a validade da consulta, os tokens, a estrutura analisada, a expressão de álgebra relacional e os grafos não otimizado e otimizado.

## Testes

Para executar os testes do backend:

```powershell
.\venv\Scripts\python.exe -m pytest backend\tests
```

Para executar os testes do frontend:

```powershell
cd frontend
npm test
```

Para verificar se o frontend compila:

```powershell
cd frontend
npm run build
```

## Endpoints principais

```text
POST /api/v1/queries/parse   Analisa e otimiza uma consulta SQL
GET  /api/v1/queries/schema  Retorna o catálogo de tabelas e campos
GET  /api/v1/health          Verifica se o backend está funcionando
```

Exemplo de requisição:

```json
{
  "sql": "SELECT Nome FROM Cliente WHERE idCliente >= 10;"
}
```

## Organização do projeto

```text
backend/
  app/
    api/              Rotas HTTP
    application/      Orquestração do processamento da consulta
    domain/           Tokenizer, parser, AST, validação, álgebra e otimização
    infrastructure/   Catálogo em memória do esquema BD_Vendas
    schemas/          Modelos de entrada e saída da API
    static/           Build do frontend para execução monolítica
  tests/              Testes do backend

frontend/
  src/app/
    core/             Serviços e modelos compartilhados
    features/         Editor, página de análise e visualização dos grafos

scripts/              Instalação, execução e build
main.py               Atalho para iniciar o backend pela raiz
```

## Solução de problemas

Se a página ficar carregando sem terminar, confirme se o backend está ativo:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

O resultado esperado é:

```text
status
------
ok
```

Se estiver usando `localhost:4200`, mantenha os dois terminais em execução. Se estiver usando o modo monolítico em `localhost:8000`, execute o build antes de iniciar o servidor.
