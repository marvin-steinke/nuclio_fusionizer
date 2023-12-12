import pytest
from fastapi.testclient import TestClient

from nuclio_fusionizer_server.main import main

# Assuming your main function returns the FastAPI app instance
app = main()

# Create a TestClient instance
client = TestClient(app)


def test_deploy():
    # test logic for the /deploy/ endpoint
    response = client.put("/deploy/", data={"function_name": "test_function"})
    assert response.status_code == 200
    assert response.json() == {"status": "success"}


def test_delete():
    # test logic for the /delete/ endpoint
    response = client.delete("/delete/test_function")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "function_name": "test_function"}


def test_get():
    # test logic for the /get/ endpoint
    response = client.get("/get/test_function")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "function_name": "test_function"}


def test_invoke():
    # test logic for the /invoke/ endpoint
    response = client.post("/invoke/test_function")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "function_name": "test_function"}


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__])
