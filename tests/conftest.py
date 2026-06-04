import pytest
from src.clients.api_client import APIClient
from src.config import BASE_URL


@pytest.fixture(scope="session")
def client() -> APIClient:
    """Session-scoped API client — one instance for the entire test run."""
    return APIClient(base_url=BASE_URL)
