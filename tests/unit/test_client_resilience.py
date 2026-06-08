"""Unit tests for APIClient's resilience layer (retries + timeout).

The live API is healthy, so these failure conditions never occur against it —
we stub the dependency with ``responses`` and script them ourselves.
"""

import allure
import pytest
import requests
import responses

from src.clients.api_client import APIClient

STUB_BASE_URL = "https://api.test.local"


@pytest.fixture
def client() -> APIClient:
    """A fresh client per test, pointed at the stubbed host."""
    return APIClient(base_url=STUB_BASE_URL)


@allure.feature("HTTP client resilience")
@allure.story("Retry policy")
@allure.severity(allure.severity_level.CRITICAL)
class TestRetryPolicy:
    @responses.activate
    def test_retries_transient_5xx_then_succeeds(self, client):
        """Fail twice with 503, then recover with 200: the client surfaces the
        success and the call count confirms all three attempts ran."""
        url = f"{STUB_BASE_URL}/posts/1"
        responses.add(responses.GET, url, status=503)
        responses.add(responses.GET, url, status=503)
        responses.add(responses.GET, url, json={"id": 1}, status=200)

        response = client.get("/posts/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1
        assert len(responses.calls) == 3

    @responses.activate
    def test_does_not_retry_post(self, client):
        """POST is excluded from retries, so a 503 surfaces immediately."""
        url = f"{STUB_BASE_URL}/posts"
        responses.add(responses.POST, url, status=503)

        response = client.post("/posts", {"title": "x"})

        assert response.status_code == 503
        assert len(responses.calls) == 1


@allure.feature("HTTP client resilience")
@allure.story("Timeout")
@allure.severity(allure.severity_level.NORMAL)
class TestTimeout:
    @responses.activate
    def test_raises_when_server_does_not_respond(self, client):
        """A request that never completes must raise rather than hang."""
        url = f"{STUB_BASE_URL}/posts/1"
        responses.add(responses.GET, url, body=requests.exceptions.ConnectTimeout())

        with pytest.raises(requests.exceptions.RequestException):
            client.get("/posts/1")
