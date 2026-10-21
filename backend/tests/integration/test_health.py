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
    assert body["optimized_algebra"] == "π[Nome](Cliente)"
    assert body["optimized_graph"]["directed"] is True
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
    assert response.json()["optimized_algebra"] is None
    assert response.json()["optimized_graph"] is None


def test_parser_endpoint_returns_syntax_errors() -> None:
    response = client.post(
        "/api/v1/queries/parse",
        json={"sql": "SELECT FROM Cliente;"},
    )

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["errors"][0]["code"] == "SYNTAX_ERROR"
