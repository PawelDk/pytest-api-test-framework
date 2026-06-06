# pytest-api-test-framework

![CI](https://github.com/PawelDk/pytest-api-test-framework/actions/workflows/ci.yml/badge.svg)
[![Allure Report](https://img.shields.io/badge/report-Allure-blueviolet)](https://paweldk.github.io/pytest-api-test-framework/)

A production-style API test framework built with Python and pytest, demonstrating multi-layer test architecture, parallel execution, and clean separation between test infrastructure and test logic.

Built against [JSONPlaceholder](https://jsonplaceholder.typicode.com) — a free public REST API.

> **Note:** With JSONPlaceholder all write operations (POST, PUT, DELETE) are simulated by the API and do not persist.

---

## Tech Stack

- **Python 3.13**
- **pytest** — test runner
- **requests** — HTTP client
- **pydantic** — response schema validation
- **pytest-xdist** — parallel test execution
- **responses** — HTTP stubbing for the offline resilience tests
- **Allure** — interactive HTML reports with run-over-run trend history

---

## Project Structure

```
pytest-api-test-framework/
├── src/
│   ├── config.py              # Env-driven config (API_BASE_URL)
│   ├── clients/
│   │   └── api_client.py       # Session-based HTTP client wrapper
│   ├── models/
│   │   └── responses.py        # Pydantic response schemas
│   └── helpers/
│       └── builders.py         # Test data factories
├── tests/
│   ├── conftest.py             # Shared fixtures (session-scoped client)
│   ├── component/
│   │   ├── test_posts.py       # Single-endpoint tests (GET, POST, PUT, DELETE)
│   │   ├── test_users.py       # User schema contract + 404 path
│   │   └── test_comments.py    # Comment schema contract + 404 path
│   ├── integration/
│   │   └── test_resource_flows.py  # Cross-resource chained tests
│   └── unit/
│       └── test_client_resilience.py  # Offline client tests (mocked retries, timeout)
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI pipeline
├── pytest.ini                  # Test config: markers, CLI options, output paths
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
python -m pytest tests/unit/
```

**Run only the offline tests** (no network — the live API isn't required):
```bash
python -m pytest -m "not live"   # just the stubbed resilience tests
python -m pytest -m live         # only the tests that hit the real API
```

**Target a local mirror or proxy:** the base URL defaults to the public JSONPlaceholder instance and is overridable via an environment variable, so you can point the suite at a local mirror or proxy of the same API without a code change:
```bash
API_BASE_URL=http://localhost:3000 python -m pytest
```

---

## Reports

Tests emit [Allure](https://allurereport.org/) result files (and a JUnit XML) on every run, which render into an interactive HTML report with steps, timings, and history.

**View the latest report:** 📊 **[paweldk.github.io/pytest-api-test-framework](https://paweldk.github.io/pytest-api-test-framework/)** — published to GitHub Pages on every push to `main`, including a **trend graph** of pass-rate and duration across runs.

**Generate it locally** (requires the Allure CLI — `brew install allure`):
```bash
python -m pytest          # writes raw results to allure-results/
allure serve allure-results   # builds and opens the report in your browser
```

When running in parallel with `-n auto`, results from all workers are collected into the same `allure-results/` directory and combined into a single report.

**In CI**, every run (including pull requests and failed runs) uploads the raw `allure-results/` and `reports/junit.xml` as a downloadable **`test-results`** artifact; pushes to `main` additionally publish the rendered report to the Pages link above.

---

## Architecture Notes

### HTTP Client Wrapper

Rather than calling `requests` directly in tests, all HTTP calls go through a thin `APIClient` wrapper (`src/clients/api_client.py`). This centralizes cross-cutting concerns in one place instead of scattering them across tests:

- **Default timeout** — every request carries a 10s timeout (overridable per call), so a hung connection fails fast instead of blocking the run indefinitely.
- **Automatic retries** — transient failures (dropped connections and `429`/`500`/`502`/`503`/`504` responses) are retried with exponential backoff via urllib3's `Retry`. `POST` is deliberately excluded, since retrying a create whose response was lost could produce a duplicate; `GET`/`PUT`/`DELETE` are safe to repeat.
- **Default headers** — JSON `Accept`/`Content-Type` and a `User-Agent` are set once on the session.
- **Request logging** — every call funnels through a single internal `_request` method that logs the method, URL, status code, and elapsed time.

Adding the next cross-cutting concern (e.g. auth) means changing the client once, not every test.

### Schema Validation

Responses are validated against [pydantic](https://docs.pydantic.dev/) models (`src/models/responses.py`) rather than poking at the raw JSON dict. A single `Post.model_validate(response.json())` asserts the entire contract at once — every field is present *and* has the expected type — so a response that returned `"id": "abc"` instead of a number fails the test, where a `"id" in data` key-check would have passed.

- **Typed access** — tests work with `post.user_id` (an attribute the IDE understands) instead of `response.json()["userId"]` (a string key that fails silently on a typo).
- **camelCase ↔ snake_case** — the API speaks `userId`/`postId`; the models expose readable `user_id`/`post_id` via field aliases.
- **Deep + format validation** — `User` validates nested `address`/`company` objects, and email fields use pydantic's `EmailStr` to validate format, not just presence.
- **List validation** — `TypeAdapter(list[Post])` validates a whole JSON array in one call, reporting the offending index and field on failure.

### Session-Scoped Fixture

The `client` fixture in `conftest.py` is scoped to the test session (`scope="session"`), meaning a single `APIClient` instance is shared across all tests in a run. This reuses the underlying `requests.Session` and avoids the overhead of creating a new HTTP connection for every test. It works safely because the client holds no mutable test state — only the base URL and session configuration.

### Parallel Safety

Tests are designed to be parallel-safe by construction:

- No shared mutable state between tests
- No test depends on the execution order of another
- Each test is self-contained — it sets up its own data via builders and asserts only on its own response

This allows `pytest-xdist` to distribute tests across workers (`-n auto`) without risk of interference.

### Test Layers

**Unit tests** (`tests/unit/`) exercise the `APIClient` in isolation with the network stubbed (`responses`) — covering the retry and timeout behaviour that a healthy live API never triggers. They run fully offline and are the only tests that exercise the resilience layer. The live tests are tagged with a `live` marker, so this hermetic subset runs on its own via `pytest -m "not live"`.

**Component tests** (`tests/component/`) validate individual endpoints in isolation — one API call per test, asserting only on that response. They are fast and pinpoint failures to a single endpoint.

**Integration tests** (`tests/integration/`) chain multiple API calls across resources to validate cross-resource relationships — for example, creating a post and then posting a comment against the returned ID, asserting the comment references the correct post. These catch contract issues that component tests cannot surface.

### Test Data Factories

`src/helpers/builders.py` provides factory functions (`build_post`, `build_comment`) that produce valid payloads with sensible defaults and optional overrides. This keeps test data construction out of test logic and makes parametrization straightforward.

---

## Test Coverage Summary

| Layer | File | Tests |
|-------|------|------:|
| Component | `test_posts.py` | 14 |
| Component | `test_users.py` | 3 |
| Component | `test_comments.py` | 3 |
| Integration | `test_resource_flows.py` | 9 |
| Unit | `test_client_resilience.py` | 3 |
| **Total** | | **32** |

**Unit layer covers:** retry on transient 5xx (fail-twice-then-succeed), POST deliberately not retried, timeout surfaced instead of hanging.

**Component layer covers:** GET all posts, GET single post, GET non-existent post (404), parametrized multi-post retrieval, POST, PUT, DELETE; plus User and Comment schema guardians and their 404 paths.

**Integration layer covers:** user→posts ownership, multi-user post retrieval, user existence guard, post→comments relationship, comment creation chain, cross-resource write→read flow.