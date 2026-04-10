import pytest
from src.clients.api_client import APIClient

BASE_URL = "https://jsonplaceholder.typicode.com"


@pytest.fixture(scope="session")
def client() -> APIClient:
    """Session-scoped API client — one instance for the entire test run."""
    return APIClient(base_url=BASE_URL)
