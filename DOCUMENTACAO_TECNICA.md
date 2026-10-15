# Documentação técnica — Processador de Consultas

## 1. Visão geral

O projeto implementa a primeira etapa de um processador acadêmico de consultas SQL. A aplicação recebe uma consulta pela interface Angular, separa a string em tokens, verifica sua estrutura sintática, cria uma representação interna e valida tabelas e campos com base no esquema `BD_Vendas`.

A arquitetura é um **monólito modular web**:

- o frontend Angular fornece a interface gráfica;
- o backend FastAPI expõe a API e contém todas as regras de negócio;
- em desenvolvimento, Angular e FastAPI executam em servidores separados;
- na versão compilada, o FastAPI também serve os arquivos estáticos do Angular;
- NetworkX e Cytoscape.js estão previstos para as próximas entregas, mas o grafo ainda não é construído.

## 2. Escopo implementado

O subconjunto SQL atualmente aceito possui:

- `SELECT`;
- `FROM`;
- `WHERE`;
- `INNER JOIN ... ON`;
- operador lógico `AND`;
- operadores `=`, `>`, `<`, `<=`, `>=` e `<>`;
- parênteses em expressões;
- campos simples, como `Nome`;
- campos qualificados, como `Cliente.Nome`;
- números inteiros e decimais;
- textos entre aspas simples;
- ponto e vírgula opcional;
- palavras-chave sem diferenciação entre maiúsculas e minúsculas.

Não fazem parte do escopo atual:

- `OR`, `NOT`, `LIKE`, `IN` e `BETWEEN`;
- `INSERT`, `UPDATE`, `DELETE` e `DROP`;
- aliases;
- funções e agregações;
- `GROUP BY` e `ORDER BY`;
- subconsultas;
- `SELECT *`;
- execução real da consulta em um banco;
- construção e visualização do grafo de operadores.

## 3. Arquitetura

```text
Navegador
   │
   ▼
Angular
   │ POST /api/v1/queries/parse
   ▼
FastAPI
   │
   ▼
QueryService
   ├── Tokenizer
   ├── Parser
   └── QueryValidator
         │
         ▼
   Catálogo BD_Vendas
```

As responsabilidades estão divididas da seguinte maneira:

| Camada | Responsabilidade |
|---|---|
| Frontend | Entrada da consulta e apresentação dos resultados |
| API | Tradução entre HTTP/JSON e os objetos internos |
| Application | Orquestração do caso de uso de análise |
| Domain | Tokenização, parsing, AST, erros e validação |
| Infrastructure | Catálogo conhecido de tabelas e campos |

## 4. Estrutura de diretórios

```text
AV2_ProjetoBD/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes.py
│   │   │   └── query_routes.py
│   │   ├── application/
│   │   │   └── query_service.py
│   │   ├── domain/
│   │   │   ├── ast_models.py
│   │   │   ├── errors.py
│   │   │   ├── graph_builder.py
│   │   │   ├── models.py
│   │   │   ├── parser.py
│   │   │   ├── tokenizer.py
│   │   │   ├── tokens.py
│   │   │   └── validator.py
│   │   ├── infrastructure/
│   │   │   └── schema_catalog.py
│   │   ├── schemas/
│   │   │   └── query_schemas.py
│   │   ├── static/
│   │   └── main.py
│   ├── tests/
│   │   ├── integration/
│   │   └── unit/
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/services/
│   │   │   ├── features/query-processor/
│   │   │   └── shared/models/
│   │   ├── index.html
│   │   ├── main.ts
│   │   └── styles.css
│   ├── angular.json
│   ├── package.json
│   ├── package-lock.json
│   ├── proxy.conf.json
│   └── tsconfig*.json
├── scripts/
├── main.py
├── README.md
├── MAPEAMENTO_PRIMEIRA_ENTREGA.md
└── DOCUMENTACAO_TECNICA.md
```

Os arquivos `__init__.py` identificam diretórios Python como pacotes e documentam a finalidade de cada pacote. Os arquivos `.gitkeep` mantêm no Git diretórios que ainda não possuem arquivos permanentes, como `static` e `public`.

## 5. Fluxo completo de uma consulta

Considere a consulta:

```sql
SELECT Cliente.Nome, Pedido.idPedido
FROM Cliente
INNER JOIN Pedido
ON Cliente.idCliente = Pedido.Cliente_idCliente
WHERE Pedido.ValorTotalPedido >= 500;
```

O fluxo é:

1. `QueryEditorComponent` captura o texto.
2. `QueryPageComponent.analyze()` chama `QueryApiService.analyze()`.
3. O serviço Angular envia `POST /api/v1/queries/parse` com `{ "sql": "..." }`.
4. `parse_query()` recebe e valida o formato do corpo HTTP com Pydantic.
5. `QueryService.analyze()` inicia o processamento.
6. `Tokenizer.tokenize()` transforma a string em objetos `Token`.
7. `Parser.parse()` consome os tokens e cria uma `Query`, que é a AST.
8. `QueryValidator.validate()` verifica tabelas e campos contra `SCHEMA_CATALOG`.
9. `QueryService` cria um `QueryAnalysisResult`.
10. A rota converte a AST para `ParsedQuery` e retorna JSON.
11. O Angular armazena a resposta.
12. `ValidationMessagesComponent` mostra sucesso ou erros.
13. `ParseResultComponent` mostra tokens e a consulta estruturada.
14. `GraphViewerComponent` continua como placeholder enquanto o grafo não estiver implementado.

## 6. Backend

### 6.1 `main.py` da raiz

É um atalho para executar o backend a partir da raiz do projeto:

```text
python main.py
```

Ele chama o Uvicorn usando `backend.app.main:app`, endereço `127.0.0.1`, porta `8000` e recarga automática.

### 6.2 `backend/app/main.py`

É o ponto de entrada da aplicação FastAPI.

Constantes:

- `APP_DIR`: diretório físico de `backend/app`;
- `STATIC_ROOT`: diretório destinado ao build Angular;
- `ANGULAR_ROOT`: procura primeiro `static/dist/browser`, depois caminhos alternativos.

Objeto `app`:

- define título, versão e descrição da API;
- inclui todas as rotas com o prefixo `/api/v1`.

Função `serve_angular(full_path)`:

- atende qualquer rota que não pertença à API;
- se o Angular não estiver compilado, retorna uma mensagem orientando executar o build;
- serve arquivos reais, como JavaScript e CSS;
- para rotas desconhecidas, devolve `index.html`, comportamento necessário para uma SPA;
- verifica se o caminho solicitado permanece dentro da pasta estática.

### 6.3 `backend/app/api/routes.py`

Centraliza as rotas da API.

- `api_router`: roteador principal da versão 1;
- `include_router(query_router)`: adiciona os endpoints de consulta;
- `health_check()`: responde `{"status": "ok"}` em `GET /api/v1/health`.

O health check serve para verificar rapidamente se o backend está ativo.

### 6.4 `backend/app/api/query_routes.py`

Expõe os endpoints relacionados às consultas.

Objetos:

- `router`: possui prefixo `/queries`;
- `service`: instância de `QueryService`.

Função `_format_field(field)`:

- transforma `FieldReference(name="Nome")` em `Nome`;
- transforma `FieldReference(name="Nome", table="Cliente")` em `Cliente.Nome`.

Função `_serialize_query(query)`:

- recebe a AST ou `None`;
- converte campos, joins e `WHERE` para o modelo Pydantic `ParsedQuery`;
- usa `asdict()` para converter dataclasses aninhadas em dicionários serializáveis.

Função `parse_query(payload)`:

- implementa `POST /api/v1/queries/parse`;
- envia `payload.sql` ao serviço;
- remove o token interno `EOF` da resposta visual;
- serializa a AST;
- converte erros internos em `ApiError`;
- retorna tokens, consulta, erros e futuro grafo.

Função `get_schema()`:

- implementa `GET /api/v1/queries/schema`;
- retorna o catálogo completo de tabelas e campos.

### 6.5 `backend/app/schemas/query_schemas.py`

Define os contratos HTTP usando Pydantic.

`ParseQueryRequest`:

- representa a requisição;
- exige a propriedade `sql`;
- impede string vazia por meio de `min_length=1`.

`ApiError`:

- possui `code`, `message` e `position` opcional.

`ParsedQuery`:

- representa a AST serializada;
- publica `select_fields` com o nome JSON `select`;
- publica `from_table` com o nome JSON `from`;
- contém `joins` e `where`.

`ParseQueryResponse`:

- `valid`: resultado final da validação;
- `tokens`: lexemas encontrados;
- `query`: consulta estruturada ou `null`;
- `errors`: lista de erros;
- `graph`: reservado ao grafo futuro.

### 6.6 `backend/app/application/query_service.py`

Contém a classe `QueryService`, fachada do caso de uso.

Método `analyze(sql)`:

1. executa o tokenizador;
2. executa o parser;
3. captura `QueryLexicalError` e devolve `LEXICAL_ERROR`;
4. captura `QuerySyntaxError` e devolve `SYNTAX_ERROR` com os tokens já reconhecidos;
5. chama o validador com a AST e o catálogo;
6. define `valid` como verdadeiro quando a lista de erros está vazia;
7. devolve `QueryAnalysisResult`.

Esse serviço mantém as rotas HTTP simples e concentra a ordem do processamento.

### 6.7 `backend/app/domain/tokens.py`

`TokenType` é um `StrEnum` com todas as categorias léxicas:

- `KEYWORD`;
- `IDENTIFIER`;
- `NUMBER`;
- `STRING`;
- `OPERATOR`;
- `COMMA`;
- `DOT`;
- `LEFT_PAREN`;
- `RIGHT_PAREN`;
- `SEMICOLON`;
- `EOF`.

`Token` é uma dataclass imutável com:

- `type`: categoria;
- `lexeme`: texto original;
- `position`: índice inicial na string SQL.

`frozen=True` impede alteração acidental. `slots=True` reduz atributos dinâmicos e deixa a estrutura mais explícita.

### 6.8 `backend/app/domain/tokenizer.py`

Responsável pela análise léxica.

Constante `KEYWORDS`:

- contém `SELECT`, `FROM`, `WHERE`, `INNER`, `JOIN`, `ON` e `AND`;
- usa `frozenset` por ser uma coleção constante com busca rápida.

Constante `SYMBOLS`:

- relaciona vírgula, ponto, parênteses e ponto e vírgula aos respectivos `TokenType`.

Método `_classify(lexeme)`:

- normaliza uma cópia do texto para reconhecer palavras-chave sem diferenciar caixa;
- verifica símbolos;
- reconhece operadores;
- reconhece inteiros e decimais;
- reconhece textos entre aspas simples;
- reconhece identificadores iniciados por letra ou `_`;
- gera erro se o lexema não se encaixar em nenhuma categoria.

Método `tokenize(sql)`:

- usa uma expressão regular para localizar lexemas na string original;
- preserva a posição com `match.start()`;
- usa `cursor` para detectar caracteres ignorados entre correspondências;
- permite espaços, tabs e quebras de linha;
- lança `QueryLexicalError` quando encontra texto inválido;
- cria e acumula objetos `Token`;
- adiciona `EOF` na posição `len(sql)`;
- retorna a lista de tokens.

O token `EOF` não aparece na interface. Ele existe para o parser saber que a entrada terminou corretamente.

### 6.9 `backend/app/domain/ast_models.py`

Define a AST, ou árvore sintática abstrata.

`FieldReference`:

- representa um campo;
- `name` é obrigatório;
- `table` é opcional.

`Literal`:

- representa texto, inteiro ou decimal presente em uma condição.

`Operand`:

- alias de tipo que permite `FieldReference` ou `Literal`.

`Comparison`:

- representa `operando operador operando`;
- exemplo: `Preco >= 100`.

`AndExpression`:

- possui uma expressão à esquerda e outra à direita;
- representa duas condições ligadas por `AND`.

`Expression`:

- alias para `Comparison` ou `AndExpression`.

`Join`:

- contém a tabela adicionada pela junção;
- contém a expressão da cláusula `ON`.

`Query`:

- `fields`: campos projetados pelo `SELECT`;
- `from_table`: tabela principal;
- `joins`: lista de junções;
- `where`: expressão de filtro opcional.

### 6.10 `backend/app/domain/parser.py`

Implementa um parser descendente simples. Ele mantém:

- `tokens`: lista recebida do tokenizador;
- `current`: índice do token atual.

Método `_current_token()`:

- devolve o token apontado por `current`.

Método `_advance()`:

- devolve o token atual;
- avança uma posição, exceto quando já está em `EOF`.

Método `_expect_keyword(keyword)`:

- exige uma palavra-chave específica;
- compara sem diferenciar maiúsculas de minúsculas;
- gera `QuerySyntaxError` com posição quando não encontra o esperado;
- avança quando encontra.

Método `_expect_type(expected_type, message)`:

- exige uma categoria de token;
- usa a mensagem recebida em caso de erro;
- avança quando a categoria está correta.

Métodos `_check_type()` e `_check_keyword()`:

- apenas verificam o token atual;
- não avançam e não lançam erro;
- são usados para partes opcionais ou repetitivas.

Método `_parse_field()`:

- lê um identificador;
- se houver ponto, lê o segundo identificador;
- cria campo simples ou qualificado.

Método `_parse_field_list()`:

- lê o primeiro campo;
- continua lendo enquanto houver vírgulas;
- retorna `list[FieldReference]`.

Método `_parse_operand()`:

- converte identificador em campo;
- converte número sem ponto em `int`;
- converte número com ponto em `float`;
- remove aspas externas de textos;
- gera erro quando o elemento não pode ser usado em uma comparação.

Método `_parse_comparison()`:

- lê operando esquerdo;
- exige operador;
- lê operando direito;
- cria `Comparison`.

Método `_parse_condition()`:

- se encontrar `(`, analisa uma expressão e exige `)`;
- caso contrário, analisa uma comparação.

Método `_parse_expression()`:

- analisa a primeira condição;
- enquanto encontrar `AND`, analisa a condição seguinte;
- cria objetos `AndExpression` encadeados.

Método `_parse_join()`:

- exige `INNER JOIN`;
- lê a tabela;
- exige `ON`;
- analisa a expressão de junção;
- cria `Join`.

Método `parse(tokens)`:

1. reinicia o estado interno;
2. exige `SELECT`;
3. lê os campos;
4. exige `FROM` e a tabela principal;
5. lê zero ou mais joins;
6. lê `WHERE` opcional;
7. consome `;` opcional;
8. exige `EOF`, rejeitando tokens extras;
9. devolve a AST `Query`.

Gramática equivalente:

```text
query       := SELECT fields FROM table joins? where? semicolon? EOF
fields      := field (COMMA field)*
field       := IDENTIFIER (DOT IDENTIFIER)?
joins       := (INNER JOIN IDENTIFIER ON expression)*
where       := WHERE expression
expression  := condition (AND condition)*
condition   := comparison | LEFT_PAREN expression RIGHT_PAREN
comparison  := operand OPERATOR operand
operand     := field | NUMBER | STRING
```

### 6.11 `backend/app/domain/validator.py`

Executa a validação semântica após o parsing.

Método `_validate_field()`:

- normaliza nomes com `casefold()`;
- para campo qualificado, verifica se a tabela existe;
- verifica se a tabela participa da consulta;
- verifica se o campo pertence à tabela;
- para campo sem qualificador, procura o campo em todas as tabelas participantes;
- gera `UNKNOWN_FIELD` quando não encontra;
- gera `AMBIGUOUS_FIELD` quando encontra em mais de uma tabela.

Método `_validate_expression()`:

- percorre recursivamente a árvore de expressões;
- em uma `Comparison`, valida operandos que sejam campos;
- ignora operandos literais;
- em `AndExpression`, valida os dois lados.

Método `validate(query, catalog)`:

1. cria mapas normalizados de tabelas e campos;
2. reúne a tabela principal e tabelas dos joins;
3. valida a existência das tabelas;
4. valida campos do `SELECT`;
5. valida condições de todos os joins;
6. valida o `WHERE`;
7. remove mensagens duplicadas por código e texto;
8. retorna a lista de `QueryError`.

Códigos semânticos:

| Código | Significado |
|---|---|
| `UNKNOWN_TABLE` | tabela inexistente no catálogo |
| `TABLE_NOT_IN_QUERY` | tabela existe, mas não está no `FROM` ou `JOIN` |
| `UNKNOWN_FIELD` | campo inexistente |
| `AMBIGUOUS_FIELD` | campo sem prefixo existe em mais de uma tabela participante |

### 6.12 `backend/app/domain/errors.py`

`QueryError`:

- dataclass retornada ao cliente;
- guarda código, mensagem e posição opcional.

`QueryLexicalError`:

- exceção lançada pelo tokenizador;
- possui mensagem e posição.

`QuerySyntaxError`:

- exceção lançada pelo parser;
- possui mensagem e posição.

As exceções interrompem a fase atual; o `QueryService` converte essas exceções em `QueryError` para a API.

### 6.13 `backend/app/domain/models.py`

`QueryAnalysisResult` transporta o resultado entre a aplicação e a API:

- `valid`;
- lista de tokens;
- AST opcional;
- lista de erros;
- grafo opcional.

Os `default_factory` criam listas novas para cada instância, evitando compartilhamento acidental de listas mutáveis.

### 6.14 `backend/app/domain/graph_builder.py`

Define `GraphBuilder` e o futuro método `build(query)`.

Atualmente lança `NotImplementedError`, intencionalmente. Nas próximas etapas, deverá:

- receber a AST;
- criar um `networkx.DiGraph`;
- adicionar operadores, tabelas e predicados;
- exportar o grafo como JSON para o Angular.

Esse arquivo não participa do fluxo da primeira entrega.

### 6.15 `backend/app/infrastructure/schema_catalog.py`

Contém `SCHEMA_CATALOG`, dicionário derivado do banco `BD_Vendas` fornecido pelo enunciado.

Cada chave é uma tabela e cada valor é sua lista de campos. O validador usa esse catálogo sem precisar conectar ao MySQL.

Tabelas disponíveis:

- `Categoria`;
- `Produto`;
- `TipoCliente`;
- `Cliente`;
- `TipoEndereco`;
- `Endereco`;
- `Telefone`;
- `Status`;
- `Pedido`;
- `Pedido_has_Produto`.

### 6.16 Configuração e dependências do backend

`backend/requirements.txt` fixa:

- FastAPI e Pydantic para API e contratos;
- Uvicorn para o servidor;
- NetworkX para a próxima etapa;
- Pytest e HTTPX para testes.

`backend/pytest.ini`:

- define `tests` como diretório de testes;
- reconhece arquivos `test_*.py`;
- usa saída resumida;
- desativa o cache do Pytest para evitar problemas de permissão no diretório sincronizado.

## 7. Frontend

### 7.1 `frontend/src/index.html`

Documento HTML base da SPA.

- define idioma `pt-BR`;
- configura codificação UTF-8 e viewport;
- contém `<app-root>`, onde o Angular monta a aplicação.

### 7.2 `frontend/src/main.ts`

Inicializa a aplicação standalone com:

- `AppComponent` como componente raiz;
- `appConfig` como conjunto de providers;
- captura de falhas de inicialização no `console.error`.

### 7.3 `frontend/src/styles.css`

Define estilos globais:

- fonte e cores básicas;
- `box-sizing` consistente;
- tamanho mínimo da página;
- herança de fonte em botões e textarea;
- cursor de botão.

### 7.4 `app.component.*`

`AppComponent` é o componente raiz standalone.

- importa `RouterOutlet`;
- seu HTML contém apenas `<router-outlet />`;
- o CSS garante altura mínima da tela;
- o teste confirma que o componente pode ser criado.

### 7.5 `app.config.ts`

Configura providers globais:

- listener global de erros do navegador;
- `HttpClient`, usado pela API;
- roteador Angular com as rotas da aplicação.

### 7.6 `app.routes.ts`

Define:

- rota vazia apontando para `QueryPageComponent`;
- título da página;
- fallback `**`, que redireciona endereços desconhecidos para a tela principal.

### 7.7 `shared/models/query.models.ts`

Contém as interfaces TypeScript equivalentes aos contratos do backend.

`QueryRequest`:

- corpo enviado à API.

`QueryError`:

- código, mensagem e posição.

`ParsedQuery`:

- campos `select`, `from`, `joins` e `where`.

`GraphNode`, `GraphEdge` e `GraphData`:

- contratos reservados à visualização futura com Cytoscape.js.

`QueryAnalysisResponse`:

- resposta completa recebida do backend.

Essas interfaces oferecem tipagem em tempo de desenvolvimento, mas não executam validação em runtime.

### 7.8 `core/services/query-api.service.ts`

`QueryApiService` centraliza a comunicação HTTP.

- `providedIn: 'root'` cria uma instância compartilhada;
- injeta `HttpClient`;
- define `/api/v1/queries` como URL base;
- `analyze(sql)` cria `QueryRequest` e executa `POST /parse`;
- retorna `Observable<QueryAnalysisResponse>`.

### 7.9 `query-page.component.*`

É o componente contêiner da funcionalidade.

Estado:

- `loading`: indica requisição ativa;
- `response`: guarda a resposta da API;
- `transportError`: guarda falha de comunicação.

Método `analyze(sql)`:

1. ativa loading;
2. limpa resposta e erro anteriores;
3. chama `QueryApiService`;
4. usa `finalize()` para sempre desativar loading;
5. guarda a resposta em caso de sucesso;
6. produz mensagem amigável em falha de rede.

Método `clear()`:

- remove resultado e erro de comunicação.

O template organiza editor, mensagens, resultado e placeholder do grafo. O CSS limita a largura, centraliza o conteúdo e estiliza o cabeçalho.

### 7.10 `query-editor.component.*`

Responsável pela entrada SQL.

Entradas e saídas:

- `loading`: recebido do componente pai;
- `analyzeQuery`: emite a SQL para análise;
- `clearQuery`: avisa que a consulta foi limpa.

`sqlControl`:

- `FormControl` não nulo;
- possui consulta inicial de exemplo;
- usa validação `required`.

Método `submit()`:

- remove espaços das extremidades;
- impede envio vazio ou durante outra requisição;
- marca o campo como tocado quando inválido;
- emite a SQL válida.

Método `clear()`:

- limpa o textarea;
- emite o evento de limpeza.

O template contém textarea, erro de preenchimento, botão Analisar e botão Limpar. O CSS cria o painel, editor com aparência de código e estados dos botões.

### 7.11 `parse-result.component.*`

Recebe `QueryAnalysisResponse | null`.

Quando existe resposta:

- mostra cada lexema como um elemento visual;
- informa quando não há tokens;
- mostra a consulta estruturada usando `JsonPipe`;
- informa quando um erro impediu a criação da AST.

O CSS organiza o resultado em grade responsiva e permite rolagem do JSON.

### 7.12 `validation-messages.component.*`

Recebe:

- lista de erros;
- erro de transporte;
- estado de validade.

Prioridade visual:

1. erro de comunicação;
2. mensagem de consulta válida;
3. lista de erros da consulta.

Quando a posição existe, ela é mostrada ao lado da mensagem. O CSS usa verde para sucesso e vermelho para erro.

### 7.13 `graph-viewer.component.*`

Recebe `GraphData | null`.

- se houver contrato de grafo, mostra mensagem de que a renderização será implementada;
- se for `null`, informa que o grafo pertence às próximas entregas;
- o painel tracejado diferencia visualmente a funcionalidade futura.

Cytoscape.js já está listado como dependência, mas ainda não é inicializado.

### 7.14 Configuração do frontend

`package.json`:

- define comandos `start`, `build`, `watch` e `test`;
- fixa Angular, RxJS, Cytoscape.js, TypeScript e Vitest;
- declara versões mínimas de Node e npm.

`package-lock.json`:

- fixa versões exatas de dependências diretas e transitivas;
- deve ser commitado para builds reproduzíveis.

`angular.json`:

- configura build, servidor e testes;
- usa `src/main.ts` como entrada;
- envia o build para `backend/app/static/dist`;
- define limites de tamanho do bundle;
- separa configurações de produção e desenvolvimento.

`proxy.conf.json`:

- durante `ng serve`, redireciona `/api` para `127.0.0.1:8000`;
- evita espalhar a URL do backend pelo frontend;
- evita a necessidade de CORS no desenvolvimento local.

`tsconfig.json`:

- ativa tipagem estrita;
- usa ES2022;
- configura resolução de módulos e regras do compilador Angular.

`tsconfig.app.json`:

- configura a compilação da aplicação.

`tsconfig.spec.json`:

- configura testes e tipos globais do Vitest.

## 8. Scripts PowerShell

### `scripts/setup.ps1`

- interrompe em qualquer erro;
- descobre a raiz do projeto;
- instala dependências Python no `venv`;
- entra temporariamente no frontend;
- executa `npm install`;
- retorna ao diretório anterior mesmo em caso de falha.

### `scripts/run-backend.ps1`

- inicia Uvicorn na porta `8000`;
- usa `--reload`, apropriado para desenvolvimento.

### `scripts/run-frontend.ps1`

- entra no frontend;
- executa `npm start`;
- inicia Angular em `http://localhost:4200`.

### `scripts/build.ps1`

- executa o build de produção do Angular;
- o resultado vai para `backend/app/static/dist` conforme `angular.json`.

### `scripts/run.ps1`

- inicia a versão monolítica sem recarga automática;
- o FastAPI serve API e Angular na porta `8000`.

Todos usam `try/finally` ao trocar de diretório, garantindo o retorno ao local anterior.

## 9. Contrato da API

### Health check

```http
GET /api/v1/health
```

Resposta:

```json
{
  "status": "ok"
}
```

### Catálogo

```http
GET /api/v1/queries/schema
```

Retorna o dicionário de tabelas e campos.

### Análise da consulta

```http
POST /api/v1/queries/parse
Content-Type: application/json
```

Requisição:

```json
{
  "sql": "SELECT Nome, Email FROM Cliente;"
}
```

Resposta válida:

```json
{
  "valid": true,
  "tokens": ["SELECT", "Nome", ",", "Email", "FROM", "Cliente", ";"],
  "query": {
    "select": ["Nome", "Email"],
    "from": "Cliente",
    "joins": [],
    "where": null
  },
  "errors": [],
  "graph": null
}
```

Resposta com campo inválido:

```json
{
  "valid": false,
  "tokens": ["SELECT", "Telefone", "FROM", "Cliente", ";"],
  "query": {
    "select": ["Telefone"],
    "from": "Cliente",
    "joins": [],
    "where": null
  },
  "errors": [
    {
      "code": "UNKNOWN_FIELD",
      "message": "O campo \"Telefone\" não existe nas tabelas da consulta.",
      "position": null
    }
  ],
  "graph": null
}
```

Um erro léxico ou sintático impede a AST e retorna `query: null`. Um erro semântico mantém a AST, permitindo mostrar o que foi parseado mesmo que a consulta seja inválida.

## 10. Tipos de erro

| Categoria | Código | Exemplo |
|---|---|---|
| Léxico | `LEXICAL_ERROR` | caractere `@`, `!` ou texto malformado |
| Sintático | `SYNTAX_ERROR` | `FROM` ausente ou condição incompleta |
| Semântico | `UNKNOWN_TABLE` | tabela não existe |
| Semântico | `TABLE_NOT_IN_QUERY` | qualificador não participa da consulta |
| Semântico | `UNKNOWN_FIELD` | campo não existe |
| Semântico | `AMBIGUOUS_FIELD` | campo pertence a mais de uma tabela |

Erros léxicos e sintáticos possuem posição baseada em índice zero. Erros semânticos atualmente não preservam posição porque a AST guarda significado, mas não guarda a posição original de cada nó.

## 11. Testes

### Backend

`test_parser.py` verifica:

- `SELECT` simples;
- múltiplos campos;
- campos qualificados;
- `WHERE`;
- `AND`;
- parênteses;
- `INNER JOIN`;
- comandos inválidos;
- campo ausente;
- `FROM` ausente;
- condição incompleta;
- parêntese não fechado;
- tokens extras.

`test_validator.py` verifica:

- consulta válida;
- nomes sem diferenciação de caixa;
- tabela inexistente;
- campo inexistente;
- campo na tabela errada;
- tabela fora da consulta;
- campo ambíguo;
- campo inválido no `WHERE`.

`test_health.py` verifica:

- health check;
- endpoint do catálogo;
- contrato válido do parser;
- erro semântico pela API;
- erro sintático pela API.

Comando:

```powershell
.\venv\Scripts\python.exe -m pytest backend -q -p no:cacheprovider
```

Estado verificado na primeira entrega: **23 testes aprovados**.

### Frontend

`app.component.spec.ts` confirma a criação do componente raiz.

Comando sem modo contínuo:

```powershell
Set-Location frontend
npm test -- --watch=false
```

Estado verificado na primeira entrega: **1 teste aprovado**.

Build de produção:

```powershell
Set-Location frontend
npm run build
```

## 12. Instalação e execução

### Pré-requisitos

- Python 3.13;
- Node.js 24.15 ou superior;
- npm 11 ou superior;
- PowerShell.

### Preparação automática

Na primeira execução, crie o ambiente virtual caso ele ainda não exista:

```powershell
python -m venv venv
```

Depois instale as dependências:

```powershell
.\scripts\setup.ps1
```

O script `setup.ps1` instala os pacotes dentro de um `venv` existente; ele não cria o ambiente virtual.

### Desenvolvimento

Terminal 1:

```powershell
.\scripts\run-backend.ps1
```

Terminal 2:

```powershell
.\scripts\run-frontend.ps1
```

Endereços:

- Angular: `http://127.0.0.1:4200`;
- API: `http://127.0.0.1:8000`;
- Swagger: `http://127.0.0.1:8000/docs`.

### Monólito compilado

```powershell
.\scripts\build.ps1
.\scripts\run.ps1
```

A aplicação completa fica em:

```text
http://127.0.0.1:8000
```

## 13. Arquivos da raiz

`.gitignore`:

- ignora ambiente virtual, caches, `node_modules`, cobertura, build Angular e arquivos de IDE;
- preserva `backend/app/static/.gitkeep`.

`.editorconfig`:

- padroniza UTF-8, fim de linha, indentação e espaços.

`.gitattributes`:

- padroniza arquivos de texto com LF;
- preserva CRLF para scripts PowerShell.

`.env.example`:

- documenta host e porta pretendidos;
- atualmente os scripts usam esses valores diretamente e ainda não carregam o arquivo `.env`.

`README.md`:

- fornece instruções rápidas de instalação, execução e testes.

`MAPEAMENTO_PRIMEIRA_ENTREGA.md`:

- registra requisitos, backlog, critérios de aceite e decisões arquiteturais.

`DOCUMENTACAO_TECNICA.md`:

- descreve a implementação e o fluxo real do código.

## 14. Próximas etapas

Para as próximas entregas, a evolução planejada é:

1. converter a AST para álgebra relacional;
2. implementar heurísticas de redução de tuplas;
3. implementar heurísticas de redução de atributos;
4. construir o grafo em `GraphBuilder` usando `networkx.DiGraph`;
5. serializar o grafo em JSON;
6. renderizar o grafo no Angular com Cytoscape.js;
7. gerar e exibir a ordem de execução.

O domínio atual já produz uma AST adequada para alimentar essas etapas sem alterar a interface de entrada ou o contrato principal da API.

