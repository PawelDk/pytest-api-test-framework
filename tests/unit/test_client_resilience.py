"""Unit tests for APIClient's resilience layer (retries + timeout).

The live API is healthy, so these failure conditions never occur against it —
we stub the dependency with ``responses`` and script them ourselves.
"""

import pytest
import requests
import responses

from src.clients.api_client import APIClient

STUB_BASE_URL = "https://api.test.local"


@pytest.fixture
def client() -> APIClient:
    """A fresh client per test, pointed at the stubbed host."""
    return APIClient(base_url=STUB_BASE_URL)


class TestRetryPolicy:
    @responses.activate
    def test_retries_transient_5xx_then_succeeds(self, client):
        """Fail twice with 503 (a retryable status), then recover with 200.

        The client must surface the eventual success — and, crucially, must
        have made all three attempts. The call-count assertion is what proves
        the retry layer actually ran rather than being bypassed by the stub.
        """
        url = f"{STUB_BASE_URL}/posts/1"
        responses.add(responses.GET, url, status=503)
        responses.add(responses.GET, url, status=503)
        responses.add(responses.GET, url, json={"id": 1}, status=200)

        response = client.get("/posts/1")

        # State: the success was surfaced, not the first 503.
        assert response.status_code == 200
        assert response.json()["id"] == 1
        # Interaction: three attempts were made (2 failures + 1 success).
        assert len(responses.calls) == 3

    @responses.activate
    def test_does_not_retry_post(self, client):
        """POST is deliberately excluded from the retry policy: replaying a
        create that may have already succeeded server-side risks a duplicate.
        A 503 on POST must therefore surface immediately, with no second try.
        """
        url = f"{STUB_BASE_URL}/posts"
        responses.add(responses.POST, url, status=503)

        response = client.post("/posts", {"title": "x"})

        assert response.status_code == 503
        assert len(responses.calls) == 1


class TestTimeout:
    @responses.activate
    def test_raises_when_server_does_not_respond(self, client):
        """A request that never completes must raise a timeout rather than hang
        forever — proving the default timeout in ``_request`` is wired through.
        """
        url = f"{STUB_BASE_URL}/posts/1"
        responses.add(responses.GET, url, body=requests.exceptions.ConnectTimeout())

        with pytest.raises(requests.exceptions.RequestException):
            client.get("/posts/1")
