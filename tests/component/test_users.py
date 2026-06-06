"""Component tests for the users resource against the live API.

Covers the User schema contract — including its nested address/company
objects — and the 404 path for a user that does not exist.
"""

import pytest
from pydantic import TypeAdapter

from src.models.responses import User

# Every test in this module hits the real API.
pytestmark = pytest.mark.live

UserList = TypeAdapter(list[User])


class TestUsersRead:
    """Read paths: status codes plus User schema contract."""

    def test_get_all_users_match_schema(self, client):
        response = client.get("/users")
        users = UserList.validate_python(response.json())
        assert len(users) > 0

    def test_get_single_user_matches_schema(self, client):
        response = client.get("/users/1")
        user = User.model_validate(response.json())
        assert user.id == 1

    def test_get_nonexistent_user_returns_404(self, client):
        response = client.get("/users/99999")
        assert response.status_code == 404
