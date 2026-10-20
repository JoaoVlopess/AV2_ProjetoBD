from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_schema_catalog_is_available() -> None:
    response = client.get("/api/v1/queries/schema")

    assert response.status_code == 200
    assert "Cliente" in response.json()


def test_parser_endpoint_has_the_expected_contract() -> None:
    response = client.post(
        "/api/v1/queries/parse",
        json={"sql": "SELECT Nome FROM Cliente;"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["query"]["select"] == ["Nome"]
    assert body["query"]["from"] == "Cliente"
    assert body["algebra"] == "π[Nome](Cliente)"
    assert body["graph"]["directed"] is True
    assert len(body["graph"]["elements"]["nodes"]) == 2
    assert len(body["graph"]["elements"]["edges"]) == 1
    assert body["errors"] == []


def test_parser_endpoint_returns_semantic_errors() -> None:
    response = client.post(
        "/api/v1/queries/parse",
        json={"sql": "SELECT Telefone FROM Cliente;"},
    )

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["errors"][0]["code"] == "UNKNOWN_FIELD"
    assert response.json()["algebra"] is None
    assert response.json()["graph"] is None


def test_parser_endpoint_returns_syntax_errors() -> None:
    response = client.post(
        "/api/v1/queries/parse",
        json={"sql": "SELECT FROM Cliente;"},
    )

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["errors"][0]["code"] == "SYNTAX_ERROR"


def test_parser_endpoint_returns_only_primitive_algebra_for_joins() -> None:
    response = client.post(
        "/api/v1/queries/parse",
        json={"sql": (
            "SELECT Cliente.Nome FROM Cliente "
            "INNER JOIN Pedido ON Cliente.idCliente = Pedido.Cliente_idCliente "
            "INNER JOIN Status ON Pedido.Status_idStatus = Status.idStatus "
            "WHERE Pedido.ValorTotalPedido >= 100;"
        )},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert "⋈" not in body["algebra"]
    assert body["algebra"].count("×") == 2
    nodes = [node["data"] for node in body["graph"]["elements"]["nodes"]]
    assert sum(node["kind"] == "product" for node in nodes) == 2
    assert sum(node.get("clause") == "ON" for node in nodes) == 2
    assert sum(node.get("clause") == "WHERE" for node in nodes) == 1
    assert all(node["kind"] != "join" and "⋈" not in node["label"] for node in nodes)
