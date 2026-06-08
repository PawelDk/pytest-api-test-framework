"""Component tests for the comments resource against the live API.

Covers the Comment schema contract (including email-format validation) and
the 404 path for a comment that does not exist.
"""

import pytest
from pydantic import TypeAdapter

from src.models.responses import Comment

pytestmark = pytest.mark.live

CommentList = TypeAdapter(list[Comment])


class TestCommentsRead:
    """Read paths: status codes plus Comment schema contract."""

    def test_get_all_comments_match_schema(self, client):
        response = client.get("/comments")
        comments = CommentList.validate_python(response.json())
        assert len(comments) > 0

    def test_get_single_comment_matches_schema(self, client):
        response = client.get("/comments/1")
        comment = Comment.model_validate(response.json())
        assert comment.id == 1

    def test_get_nonexistent_comment_returns_404(self, client):
        response = client.get("/comments/99999")
        assert response.status_code == 404
