# Mapeamento da primeira entrega — Processador de Consultas

**Prazo informado:** 15/10/2026  
**Escopo desta etapa:** interface gráfica, análise da string SQL e validação de comandos, tabelas e campos.

**Decisão arquitetural:** monólito modular web, com Angular na interface, FastAPI/Python no backend e NetworkX para representar os grafos.

## 1. Resultado esperado

Ao final da primeira entrega, deve ser possível:

1. abrir uma aplicação web com interface gráfica Angular;
2. digitar uma consulta SQL em um campo de texto;
3. clicar em **Analisar**;
4. separar a consulta em seus componentes (`SELECT`, `FROM`, `INNER JOIN`, `WHERE` e condições);
5. mostrar os componentes reconhecidos na tela;
6. informar de forma clara se a consulta é válida;
7. rejeitar comandos não suportados e nomes inexistentes de tabelas ou campos.

O grafo, a álgebra relacional, a otimização e o plano de execução pertencem às próximas etapas. Entretanto, o parser desta entrega deve produzir uma estrutura em memória que possa ser reutilizada nelas.

> Atenção: o PDF dá ainda **1,0 ponto separado** para “Existe local para inserir a string com a consulta SQL”. Mesmo não aparecendo na lista resumida da primeira entrega, esse item deve fazer parte da interface desde já.

## 2. Subconjunto de SQL a aceitar

O enunciado limita o parser a:

- comandos/cláusulas: `SELECT`, `FROM`, `WHERE` e `INNER JOIN`;
- comparações: `=`, `>`, `<`, `<=`, `>=` e `<>`;
- composição de condições: `AND`, `(` e `)`.


Uma forma prática de definir a sintaxe da primeira entrega é:

```text
consulta       := SELECT lista_campos FROM tabela joins? where? ponto_virgula?
lista_campos   := campo ("," campo)* | "*"
joins          := (INNER JOIN tabela ON expressao)+
where          := WHERE expressao
expressao      := comparacao | "(" expressao ")" | expressao AND expressao
comparacao     := operando operador operando
operador       := "=" | ">" | "<" | "<=" | ">=" | "<>"
operando       := campo | numero | texto
campo          := identificador | identificador "." identificador
tabela         := identificador
```

Itens necessários para tornar as consultas utilizáveis, embora não estejam enumerados como operadores no PDF: vírgula entre campos, ponto em `Tabela.campo`, cláusula `ON`, literais numéricos/textuais e `;` opcional.

### Decisões de escopo recomendadas

- palavras-chave sem distinção entre maiúsculas e minúsculas;
- nomes de tabelas e campos também comparados sem distinguir maiúsculas/minúsculas;
- espaços e quebras de linha livres;
- aceitar nome qualificado, como `Cliente.Nome`;
- aceitar `*` no `SELECT`;
- não aceitar nesta etapa: `OR`, `NOT`, `LIKE`, `IN`, `BETWEEN`, funções, agregações, `GROUP BY`, `ORDER BY`, subconsultas, `INSERT`, `UPDATE`, `DELETE` e `DROP`;
- aliases (`Cliente c`) só devem ser implementados se o professor confirmar que serão usados nos testes.

## 3. Catálogo para validação

Não é necessário criar ou conectar o MySQL para a primeira entrega. O próprio enunciado diz que o banco é opcional e fornece o esquema para validar nomes. Um catálogo em memória é suficiente:

| Tabela | Campos |
|---|---|
| `Categoria` | `idCategoria`, `Descricao` |
| `Produto` | `idProduto`, `Nome`, `Descricao`, `Preco`, `QuantEstoque`, `Categoria_idCategoria` |
| `TipoCliente` | `idTipoCliente`, `Descricao` |
| `Cliente` | `idCliente`, `Nome`, `Email`, `Nascimento`, `Senha`, `TipoCliente_idTipoCliente`, `DataRegistro` |
| `TipoEndereco` | `idTipoEndereco`, `Descricao` |
| `Endereco` | `idEndereco`, `EnderecoPadrao`, `Logradouro`, `Numero`, `Complemento`, `Bairro`, `Cidade`, `UF`, `CEP`, `TipoEndereco_idTipoEndereco`, `Cliente_idCliente` |
| `Telefone` | `Numero`, `Cliente_idCliente` |
| `Status` | `idStatus`, `Descricao` |
| `Pedido` | `idPedido`, `Status_idStatus`, `DataPedido`, `ValorTotalPedido`, `Cliente_idCliente` |
| `Pedido_has_Produto` | `idPedidoProduto`, `Pedido_idPedido`, `Produto_idProduto`, `Quantidade`, `PrecoUnitario` |

## 4. Componentes a implementar

### 4.1 Interface gráfica

Usar **Angular** como SPA (Single-Page Application). A interface não deve conhecer as regras do parser: ela envia a consulta para a API Python e apenas apresenta a resposta.

Elementos mínimos:

- título da aplicação;
- campo de texto multilinha para a consulta;
- botão **Analisar**;
- botão **Limpar**;
- área de resultado do parser;
- área de mensagens de validação;
- indicação visual de sucesso ou erro.

Organização recomendada no Angular:

```text
core/
└── services/query-api.service.ts       # comunicação HTTP com o backend
features/query-processor/
├── query-page.component.ts             # tela principal
├── query-editor.component.ts           # entrada da consulta
├── parse-result.component.ts           # componentes reconhecidos
├── validation-messages.component.ts    # erros e avisos
└── graph-viewer.component.ts            # reservado ao grafo
shared/
└── models/query.models.ts               # contratos TypeScript da API
```

Para a primeira entrega, `graph-viewer` pode ficar como espaço reservado. Ele será ativado quando o trabalho chegar à etapa de construção do grafo.

Comportamentos obrigatórios:

- a janela abre sem erro;
- o botão **Analisar** lê o texto atual;
- consulta vazia produz mensagem amigável;
- consulta válida mostra as partes reconhecidas;
- consulta inválida não encerra a aplicação e mostra onde está o problema;
- uma nova análise substitui o resultado anterior.

Também é recomendado:

- usar formulário reativo para a entrada SQL;
- desabilitar **Analisar** enquanto a requisição estiver em andamento;
- exibir indicador de carregamento;
- diferenciar erro da consulta de falha de comunicação com o backend;
- manter exemplos de consultas válidas que possam ser carregados no editor.

### 4.2 Tokenizador

Transformar a string em tokens antes de montar a consulta. Reconhecer:

- palavras-chave;
- identificadores de tabela/campo;
- números;
- textos entre aspas simples;
- `,`, `.`, `(`, `)`, `;`;
- operadores, dando prioridade a `<=`, `>=` e `<>` antes de `<` e `>`.

Saída ilustrativa:

```text
SELECT Cliente.Nome FROM Cliente WHERE Cliente.idCliente >= 10
↓
[SELECT, Cliente, ., Nome, FROM, Cliente, WHERE,
 Cliente, ., idCliente, >=, 10]
```

### 4.3 Parser

Consumir os tokens, verificar a ordem das cláusulas e produzir uma árvore/objeto estruturado. Exemplo de resultado:

```text
Consulta
├── campos: [Cliente.Nome]
├── tabelas: [Cliente]
├── joins: []
└── where
    └── comparacao: Cliente.idCliente >= 10
```

Não usar somente uma expressão regular grande. Regex funciona bem para tokenizar, mas um parser pequeno por funções facilita parênteses, `AND`, mensagens de erro e as próximas fases do trabalho.

### 4.4 Validador

Separar validação sintática de validação semântica.

**Validação sintática:**

- consulta começa com `SELECT`;
- existe ao menos um campo;
- existe `FROM` e uma tabela;
- cláusulas estão na ordem correta;
- `INNER JOIN` possui tabela, `ON` e condição;
- comparação possui dois operandos e operador permitido;
- parênteses estão balanceados;
- não há tokens inesperados após o fim da consulta;
- comandos não suportados são recusados.

**Validação semântica:**

- tabela existe no catálogo;
- todo campo existe;
- campo qualificado pertence à tabela indicada;
- tabela usada para qualificar um campo participa da consulta;
- campo sem prefixo é recusado se for ambíguo entre as tabelas participantes;
- campos de `SELECT`, `ON` e `WHERE` passam pela mesma validação.

Exemplos de mensagens úteis:

```text
Erro: comando UPDATE não é suportado. Use SELECT.
Erro: tabela "Clientes" não existe. Você quis dizer "Cliente"?
Erro: campo "Cliente.Telefone" não existe.
Erro: esperado FROM após a lista de campos.
Erro: parêntese aberto na posição 42 não foi fechado.
Erro: o campo "Descricao" é ambíguo; informe a tabela.
```

### 4.5 API Python

Usar **FastAPI** com modelos Pydantic para formalizar a entrada e a saída. A rota não deve conter as regras do parser; ela chama um serviço de aplicação, que coordena tokenizador, parser e validador.

Endpoints da primeira entrega:

| Método e rota | Finalidade |
|---|---|
| `GET /api/v1/health` | confirmar que o backend está ativo |
| `GET /api/v1/schema` | retornar o catálogo conhecido, útil para a interface e depuração |
| `POST /api/v1/queries/parse` | tokenizar, parsear e validar uma consulta |

Requisição principal:

```json
{
  "sql": "SELECT Nome, Email FROM Cliente;"
}
```

Resposta de sucesso:

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

Resposta para SQL inválido:

```json
{
  "valid": false,
  "tokens": ["SELECT", "Telefone", "FROM", "Cliente"],
  "query": null,
  "errors": [
    {
      "code": "UNKNOWN_FIELD",
      "message": "O campo Cliente.Telefone não existe.",
      "position": 7
    }
  ],
  "graph": null
}
```

Erros da linguagem SQL devem voltar como resultado de domínio (`valid: false`). Erros no formato da própria requisição HTTP, como ausência da propriedade `sql`, podem usar a validação HTTP padrão do FastAPI.

### 4.6 NetworkX e visualização do grafo

O **NetworkX roda no backend**. Ele será responsável por:

- criar o grafo direcionado de operadores;
- armazenar atributos dos nós e arestas;
- percorrer o grafo;
- apoiar a definição da ordem de execução;
- exportar nós e arestas em formato serializável.

NetworkX não desenha diretamente um componente interativo dentro do Angular. Para a visualização no navegador, usar **Cytoscape.js** no componente `graph-viewer`. O backend converte o grafo NetworkX para JSON, preferencialmente com `networkx.readwrite.json_graph.cytoscape_data()`, e o Angular entrega esses elementos ao Cytoscape.js.

```text
Parser/AST → GraphBuilder → NetworkX DiGraph → JSON → API → Angular → Cytoscape.js
```

Essa parte fica preparada na arquitetura, mas não precisa estar completa na primeira entrega. Nesta fase, a propriedade `graph` pode ser `null`.

### 4.7 Forma monolítica de execução

O projeto é um **monólito modular**:

- um único repositório;
- um único backend contendo todas as regras;
- nenhuma comunicação entre microserviços;
- uma única API;
- uma única entrega executável;
- Angular compilado e servido pelo próprio FastAPI em produção.

Durante o desenvolvimento:

```text
Navegador → Angular dev server :4200 → proxy /api → FastAPI :8000
```

Na entrega/produção:

```text
Navegador → FastAPI :8000
             ├── /api/*  → API e regras Python
             └── /*      → arquivos compilados do Angular
```

O comando `ng build` gera os arquivos de produção do Angular. O FastAPI serve esses arquivos estáticos e deve redirecionar rotas desconhecidas da SPA para `index.html`. Node.js é necessário para desenvolver e compilar a interface, mas não precisa executar em produção.

### 4.8 Responsabilidades das camadas

| Camada | Responsabilidade | Não deve fazer |
|---|---|---|
| Angular | entrada, feedback e apresentação | interpretar SQL ou validar nomes do banco |
| Rotas FastAPI | receber/retornar HTTP | implementar o parser diretamente |
| Serviço de aplicação | coordenar o caso de uso | depender de componentes visuais |
| Domínio | tokens, AST, parser, validação e grafo | conhecer HTTP ou Angular |
| Catálogo | fornecer tabelas e campos válidos | controlar a interface |
| NetworkX | estrutura e algoritmos do grafo | renderizar o componente Angular |

## 5. Estrutura de arquivos sugerida

```text
AV2_ProjetoBD/
├── backend/
│   ├── app/
│   │   ├── main.py                     # instancia o FastAPI e serve o Angular
│   │   ├── api/
│   │   │   ├── routes.py               # agrega as rotas
│   │   │   └── query_routes.py         # endpoints /api/v1/queries
│   │   ├── application/
│   │   │   └── query_service.py        # coordena o caso de uso
│   │   ├── domain/
│   │   │   ├── ast_models.py           # Consulta, Join, Comparação etc.
│   │   │   ├── tokens.py               # tokenizador
│   │   │   ├── parser.py               # análise sintática
│   │   │   ├── validator.py            # validação semântica
│   │   │   └── graph_builder.py        # integração futura com NetworkX
│   │   ├── schemas/
│   │   │   └── query_schemas.py        # contratos Pydantic da API
│   │   ├── infrastructure/
│   │   │   └── schema_catalog.py       # catálogo BD_Vendas
│   │   └── static/                      # saída compilada do Angular
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   └── requirements.txt
├── frontend/
│   ├── src/app/
│   │   ├── core/services/
│   │   ├── features/query-processor/
│   │   └── shared/models/
│   ├── proxy.conf.json                  # /api → localhost:8000
│   ├── angular.json
│   ├── package.json
│   └── package-lock.json
├── scripts/
│   ├── build.ps1                        # compila Angular para backend/app/static
│   └── run.ps1                          # inicia o monólito compilado
├── README.md
└── .gitignore
```

Fluxo recomendado:

```text
Angular → POST /api/v1/queries/parse → Serviço → Tokenizador → Parser → Validador
   ↑                                                                       │
   └──────────────────────────── resposta JSON ─────────────────────────────┘

Evolução futura no mesmo fluxo:
Parser → AST → Álgebra relacional → Otimizador → NetworkX → JSON do grafo
```

### Dependências previstas

**Backend:** `fastapi`, `uvicorn`, `pydantic`, `networkx`, `pytest` e `httpx` para testes da API.

**Frontend:** Angular/TypeScript, `HttpClient`, formulários reativos e `cytoscape` para a etapa visual do grafo.

As versões devem ficar fixadas em `requirements.txt` e `package-lock.json`, permitindo que a equipe reproduza o ambiente.

### Estratégia de testes por camada

| Tipo | Ferramenta | O que testar |
|---|---|---|
| unidade do domínio | `pytest` | tokenizador, parser, catálogo e validador sem iniciar servidor |
| integração da API | `pytest` + cliente de teste HTTP | contrato de `/api/v1/queries/parse` e códigos HTTP |
| unidade do frontend | `ng test` | serviço HTTP e estados dos componentes |
| integração manual | navegador | digitação → API → resultado/erro visível |
| build | `ng build` + inicialização do FastAPI | Angular compilado servido pelo mesmo processo |

### Cuidados para manter o monólito simples

- não criar microsserviços, filas, autenticação ou banco de dados apenas por arquitetura;
- não duplicar o parser em TypeScript: a regra existe somente no backend;
- não fazer a rota HTTP acessar diretamente detalhes do tokenizador;
- usar o proxy do Angular durante o desenvolvimento, evitando configuração CORS desnecessária;
- não versionar `node_modules`, cache Python ou arquivos temporários;
- documentar no `README.md` um comando de desenvolvimento e um comando de entrega;
- manter o NetworkX isolado em `graph_builder.py`, para que o parser continue testável sem renderização;
- tratar o JSON da API como contrato: alterações no Python devem ser refletidas nos modelos TypeScript.

### Riscos e controle de escopo

| Risco | Como controlar |
|---|---|
| Angular consumir tempo antes do parser existir | criar primeiro uma tela mínima, sem biblioteca visual pesada |
| tentar entregar o grafo antes da hora | deixar `graph: null` e o componente reservado nesta etapa |
| chamar de monólito, mas exigir dois servidores na apresentação | gerar o build Angular e servi-lo pelo FastAPI antes de 14/10 |
| regras espalhadas entre frontend e backend | manter toda análise e validação no domínio Python |
| contrato mudar e quebrar a tela | definir modelos Pydantic e interfaces TypeScript desde o início |

## 6. Backlog em ordem de execução

| Ordem | Tarefa | Entrega verificável |
|---:|---|---|
| 1 | Criar o esqueleto `backend/` e `frontend/` | FastAPI e Angular iniciam separadamente em desenvolvimento |
| 2 | Configurar o proxy `/api` do Angular | frontend acessa backend sem URL espalhada no código |
| 3 | Criar catálogo `BD_Vendas` | tabelas/campos disponíveis em memória |
| 4 | Definir modelos de domínio e contratos Pydantic | objetos da consulta e JSON da API documentados |
| 5 | Implementar tokenizador | lista correta de tokens ou erro léxico |
| 6 | Implementar parser de `SELECT` e `FROM` | consulta simples estruturada |
| 7 | Adicionar `WHERE`, comparações, `AND` e parênteses | expressão estruturada |
| 8 | Adicionar `INNER JOIN ... ON` | junção estruturada |
| 9 | Implementar validação de comandos/tabelas/campos | erros semânticos claros |
| 10 | Expor `POST /api/v1/queries/parse` | fluxo do backend testável pelo Swagger |
| 11 | Construir a GUI Angular | editor, botões, resultado e erros funcionando |
| 12 | Integrar Angular e FastAPI | fluxo completo pelo botão **Analisar** |
| 13 | Configurar build monolítico | FastAPI serve o Angular compilado |
| 14 | Criar testes e roteiro de demonstração | evidências dos critérios atendidos |
| 15 | Reservar contrato e componente do grafo | evolução com NetworkX sem refazer a arquitetura |

## 7. Casos de teste mínimos

### Devem ser aceitos

```sql
SELECT Nome, Email FROM Cliente;
```

```sql
SELECT Produto.Nome, Produto.Preco
FROM Produto
WHERE Produto.Preco >= 100 AND Produto.QuantEstoque > 0;
```

```sql
SELECT Cliente.Nome, Pedido.idPedido
FROM Cliente
INNER JOIN Pedido
ON Cliente.idCliente = Pedido.Cliente_idCliente
WHERE Pedido.ValorTotalPedido > 500;
```

```sql
SELECT Nome FROM Cliente
WHERE (idCliente >= 10 AND idCliente <= 20);
```

### Devem ser recusados

| Entrada | Motivo esperado |
|---|---|
| string vazia | consulta não informada |
| `UPDATE Cliente SET Nome = 'A'` | comando não suportado |
| `SELECT FROM Cliente` | lista de campos ausente |
| `SELECT Nome Cliente` | `FROM` ausente |
| `SELECT Nome FROM Clientes` | tabela inexistente |
| `SELECT Telefone FROM Cliente` | campo inexistente |
| `SELECT Cliente.Preco FROM Cliente` | campo não pertence à tabela |
| `SELECT Descricao FROM Produto INNER JOIN Categoria ON Produto.Categoria_idCategoria = Categoria.idCategoria` | campo `Descricao` ambíguo |
| `SELECT Nome FROM Cliente WHERE idCliente != 1` | operador não previsto (`<>` é o suportado) |
| `SELECT Nome FROM Cliente WHERE (idCliente > 1` | parêntese não fechado |
| `SELECT Nome FROM Cliente WHERE idCliente >` | operando ausente |
| `SELECT Nome FROM Cliente OR idCliente = 1` | cláusula/token não suportado |

## 8. Critérios de aceite da primeira entrega

### Interface gráfica existente e funcional — 1,5

- [ ] aplicação Angular abre no navegador;
- [ ] há campo visível para inserir SQL;
- [ ] há ação visível para analisar;
- [ ] há saída visível para resultado e erros;
- [ ] erros do usuário não fecham a aplicação.
- [ ] versão compilada da interface é servida pelo FastAPI;

### Local para inserir a consulta — 1,0 no PDF

- [ ] campo aceita consulta em uma ou várias linhas;
- [ ] texto digitado é realmente usado pelo analisador.

### A string é parseada — 1,0

- [ ] tokens são reconhecidos corretamente;
- [ ] `SELECT`, `FROM`, `WHERE` e `INNER JOIN` são separados;
- [ ] campos, tabelas e condições ficam em uma estrutura em memória;
- [ ] `AND` e parênteses são representados corretamente;
- [ ] a GUI mostra um resumo das partes encontradas.

### Campos e comandos errados são validados — 1,0

- [ ] comandos fora do subconjunto são rejeitados;
- [ ] tabelas inexistentes são rejeitadas;
- [ ] campos inexistentes ou associados à tabela errada são rejeitados;
- [ ] erros de sintaxe são explicados de forma compreensível;
- [ ] a GUI distingue claramente sucesso de erro.

## 9. Cronograma curto até 15/10/2026

| Data | Meta |
|---|---|
| 06/10 | fechar arquitetura, gramática e contratos da API |
| 07/10 | criar projetos FastAPI e Angular, proxy e tela-base |
| 08/10 | catálogo, modelos, tokenizador e testes unitários |
| 09–10/10 | parser de `SELECT`, `FROM`, `WHERE`, condições e parênteses |
| 11/10 | `INNER JOIN ... ON` e contratos preparados para o grafo |
| 12/10 | validação de comandos, tabelas, campos e ambiguidades |
| 13/10 | integrar interface Angular com a API FastAPI |
| 14/10 | build monolítico, testes, correções e ensaio da apresentação |
| 15/10 | entrega com versão estável |

## 10. Roteiro de demonstração

1. iniciar o FastAPI e abrir a aplicação Angular no navegador;
2. executar uma consulta simples válida;
3. mostrar na interface os campos, tabela e condições parseados;
4. executar uma consulta válida com `INNER JOIN`;
5. testar uma tabela inexistente;
6. testar um campo inexistente;
7. testar um comando proibido, como `UPDATE`;
8. testar um erro de sintaxe, como parêntese não fechado;
9. mostrar que a aplicação continua funcionando após todos os erros.

Também convém abrir `/docs` durante o desenvolvimento para demonstrar e testar isoladamente o endpoint do FastAPI. Na apresentação final, o fluxo principal deve continuar sendo realizado pela interface Angular.

## 11. O que esta arquitetura permite estudar

- Angular: componentes, formulários reativos, serviços, injeção de dependência e HTTP;
- TypeScript: interfaces e tipagem dos contratos JSON;
- FastAPI/Pydantic: API REST, validação de entrada e documentação automática;
- Python: tokenização, análise sintática, AST e validação semântica;
- arquitetura: separação de responsabilidades dentro de um monólito;
- NetworkX: grafos direcionados, atributos, percursos e serialização;
- Cytoscape.js: renderização e interação com o grafo no navegador;
- testes: unidade no domínio, integração na API e componentes no frontend;
- empacotamento: build Angular servido pela aplicação Python.

É uma arquitetura adequada para aprender enquanto desenvolve, desde que o grafo visual completo não seja antecipado para a primeira entrega. O caminho crítico até 15/10 continua sendo: tela Angular → API → parser → validação → resposta visível.

## 12. Referências técnicas da arquitetura

- [Build e implantação de aplicações Angular](https://angular.dev/tools/cli/deployment)
- [Arquivos estáticos no FastAPI](https://fastapi.tiangolo.com/tutorial/static-files/)
- [Corpos de requisição com Pydantic no FastAPI](https://fastapi.tiangolo.com/tutorial/body/)
- [Serialização JSON de grafos NetworkX](https://networkx.org/documentation/stable/reference/readwrite/json_graph.html)
- [Elementos e layouts do Cytoscape.js](https://js.cytoscape.org/)

## Pontos que vale confirmar com o professor

- se aliases de tabela/campo serão usados nos testes;
- se `SELECT *` precisa ser aceito;
- se `;` deve ser obrigatório ou opcional;
- se `INNER JOIN` será sempre escrito com `ON`;
- se literais de data serão cobrados;
- se a entrega precisa apenas validar a consulta ou também conectá-la ao MySQL.

Essas dúvidas não impedem o início: as decisões recomendadas acima formam um escopo coerente e extensível para a primeira versão.
