import os

# Base URL for the API under test. Overridable per environment via the
# API_BASE_URL env var; defaults to the public JSONPlaceholder instance so the
# suite runs with zero setup.
BASE_URL = os.getenv("API_BASE_URL", "https://jsonplaceholder.typicode.com")