import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10  # seconds
DEFAULT_RETRIES = 3


class APIClient:
    """Thin, resilient wrapper around requests.Session.

    Centralises base URL, default headers, request timeouts, a retry policy for
    transient failures, and request/response logging — so individual tests stay
    focused on assertions rather than HTTP plumbing.
    """

    def __init__(self, base_url: str, timeout: float = DEFAULT_TIMEOUT, retries: int = DEFAULT_RETRIES):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "pytest-api-test-framework",
        })

        # Retry transient failures (dropped connections + the listed status
        # codes) with a short, growing wait between attempts. POST is left out
        # on purpose: each POST creates a new record, so retrying one whose
        # response got lost could create a duplicate. GET/PUT/DELETE are safe
        # to repeat — running them again lands on the same result.
        retry_policy = Retry(
            total=retries,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "PUT", "DELETE"),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_policy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        return self._request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, payload: dict, **kwargs) -> requests.Response:
        return self._request("POST", endpoint, json=payload, **kwargs)

    def put(self, endpoint: str, payload: dict, **kwargs) -> requests.Response:
        return self._request("PUT", endpoint, json=payload, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        return self._request("DELETE", endpoint, **kwargs)

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Single chokepoint for every request: applies the default timeout
        (unless a caller overrides it) and logs the round trip."""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("timeout", self.timeout)

        logger.info("→ %s %s", method, url)
        response = self.session.request(method, url, **kwargs)
        logger.info(
            "← %s %s [%s] %.0fms",
            method, url, response.status_code, response.elapsed.total_seconds() * 1000,
        )
        return response
