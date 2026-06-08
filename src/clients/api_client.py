import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10  # seconds
DEFAULT_RETRIES = 3


class APIClient:
    """Wrapper around requests.Session: base URL, default headers, timeouts,
    a retry policy, and request/response logging."""

    def __init__(
        self,
        base_url: str,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "pytest-api-test-framework",
            }
        )

        # Retry transient failures on idempotent methods only. POST is excluded:
        # replaying a create whose response was lost could duplicate the record.
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
        """Applies the default timeout (unless overridden) and logs the round trip."""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("timeout", self.timeout)

        logger.info("→ %s %s", method, url)
        response = self.session.request(method, url, **kwargs)
        logger.info(
            "← %s %s [%s] %.0fms",
            method,
            url,
            response.status_code,
            response.elapsed.total_seconds() * 1000,
        )
        return response
