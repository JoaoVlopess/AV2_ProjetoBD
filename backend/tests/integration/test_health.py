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
    assert response.json()["valid"] is False
    assert response.json()["errors"][0]["code"] == "NOT_IMPLEMENTED"
