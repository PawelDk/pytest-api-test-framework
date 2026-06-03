# pytest-api-test-framework

![CI](https://github.com/PawelDk/pytest-api-test-framework/actions/workflows/ci.yml/badge.svg)

A production-style API test framework built with Python and pytest, demonstrating multi-layer test architecture, parallel execution, and clean separation between test infrastructure and test logic.

Built against [JSONPlaceholder](https://jsonplaceholder.typicode.com) — a free public REST API.

> **Note:** all write operations (POST, PUT, DELETE) are simulated by the API and do not persist.

---

## Tech Stack

- **Python 3.13**
- **pytest** — test runner
- **requests** — HTTP client
- **pytest-xdist** — parallel test execution
- **pytest-html** — HTML report generation

---

## Project Structure

```
pytest-api-test-framework/
├── src/
│   ├── clients/
│   │   └── api_client.py       # Session-based HTTP client wrapper
│   └── helpers/
│       └── builders.py         # Test data factories
├── tests/
│   ├── conftest.py             # Shared fixtures (session-scoped client)
│   ├── component/
│   │   └── test_posts.py       # Single-endpoint tests (GET, POST, PUT, DELETE)
│   └── integration/
│       └── test_resource_flows.py  # Cross-resource chained tests
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI pipeline
├── pytest.ini
└── requirements.txt
```

---

## How to Run

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Run all tests:**
```bash
python -m pytest
```

**Run in parallel:**
```bash
python -m pytest -n auto
```

**Run by layer:**
```bash
python -m pytest tests/component/
python -m pytest tests/integration/
```

**HTML report** is generated at `reports/report.html` after each run. When running in parallel with `-n auto`, results from all workers are automatically combined into a single report.

---

## Architecture Notes

### HTTP Client Wrapper

Rather than calling `requests` directly in tests, all HTTP calls go through a thin `APIClient` wrapper (`src/clients/api_client.py`). This centralises cross-cutting concerns in one place instead of scattering them across tests:

- **Default timeout** — every request carries a 10s timeout (overridable per call), so a hung connection fails fast instead of blocking the run indefinitely.
- **Automatic retries** — transient failures (dropped connections and `429`/`500`/`502`/`503`/`504` responses) are retried with exponential backoff via urllib3's `Retry`. `POST` is deliberately excluded, since retrying a create whose response was lost could produce a duplicate; `GET`/`PUT`/`DELETE` are safe to repeat.
- **Default headers** — JSON `Accept`/`Content-Type` and a `User-Agent` are set once on the session.
- **Request logging** — every call funnels through a single internal `_request` method that logs the method, URL, status code, and elapsed time.

Adding the next cross-cutting concern (e.g. auth) means changing the client once, not every test.

### Session-Scoped Fixture

The `client` fixture in `conftest.py` is scoped to the test session (`scope="session"`), meaning a single `APIClient` instance is shared across all tests in a run. This reuses the underlying `requests.Session` and avoids the overhead of creating a new HTTP connection for every test. It works safely because the client holds no mutable test state — only the base URL and session configuration.

### Parallel Safety

Tests are designed to be parallel-safe by construction:

- No shared mutable state between tests
- No test depends on the execution order of another
- Each test is self-contained — it sets up its own data via builders and asserts only on its own response

This allows `pytest-xdist` to distribute tests across workers (`-n auto`) without risk of interference.

### Component vs Integration Layer

**Component tests** (`tests/component/`) validate individual endpoints in isolation — one API call per test, asserting only on that response. They are fast and pinpoint failures to a single endpoint.

**Integration tests** (`tests/integration/`) chain multiple API calls across resources to validate cross-resource relationships — for example, creating a post and then posting a comment against the returned ID, asserting the comment references the correct post. These catch contract issues that component tests cannot surface.

### Test Data Factories

`src/helpers/builders.py` provides factory functions (`build_post`, `build_comment`) that produce valid payloads with sensible defaults and optional overrides. This keeps test data construction out of test logic and makes parametrization straightforward.

---

## Test Coverage Summary

| Layer | File | Tests |
|-------|------|------:|
| Component | `test_posts.py` | 14 |
| Integration | `test_resource_flows.py` | 9 |
| **Total** | | **23** |

**Component layer covers:** GET all posts, GET single post, GET non-existent post (404), parametrized multi-post retrieval, POST, PUT, DELETE.

**Integration layer covers:** user→posts ownership, multi-user post retrieval, user existence guard, post→comments relationship, comment creation chain, cross-resource write→read flow.