import os

# Base URL for JSONPlaceholder, the API under test. Defaults to the public instance so the suite
# runs with zero setup. Overridable via API_BASE_URL to point at a local mirror or proxy.
BASE_URL = os.getenv("API_BASE_URL", "https://jsonplaceholder.typicode.com")