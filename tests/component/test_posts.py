import pytest
from pydantic import TypeAdapter

from src.helpers.builders import build_post
from src.models.responses import Post

# Validates a JSON array of posts in one call: every element must satisfy the
# Post contract, or validation raises with the offending index and field.
PostList = TypeAdapter(list[Post])


class TestPostsRead:
    def test_get_all_posts_returns_200(self, client):
        response = client.get("/posts")
        assert response.status_code == 200

    def test_get_all_posts_match_schema(self, client):
        response = client.get("/posts")
        posts = PostList.validate_python(response.json())
        assert len(posts) > 0

    def test_get_single_post_returns_200(self, client):
        response = client.get("/posts/1")
        assert response.status_code == 200

    def test_get_single_post_matches_schema(self, client):
        response = client.get("/posts/1")
        post = Post.model_validate(response.json())
        assert post.id == 1

    def test_get_nonexistent_post_returns_404(self, client):
        response = client.get("/posts/99999")
        assert response.status_code == 404

    @pytest.mark.parametrize("post_id", [1, 2, 3, 5, 10])
    def test_multiple_posts_are_retrievable(self, client, post_id):
        response = client.get(f"/posts/{post_id}")
        assert response.status_code == 200
        assert response.json()["id"] == post_id


class TestPostsWrite:
    """
    JSONPlaceholder fakes write operations — POST/PUT/DELETE return success
    responses but do not persist. This validates request/response contract.
    """

    def test_create_post_returns_201(self, client):
        payload = build_post()
        response = client.post("/posts", payload)
        assert response.status_code == 201

    def test_create_post_reflects_sent_data(self, client):
        payload = build_post(title="Specific Title", body="Specific Body", user_id=3)
        response = client.post("/posts", payload)
        post = Post.model_validate(response.json())
        assert post.title == "Specific Title"
        assert post.body == "Specific Body"
        assert post.user_id == 3

    def test_update_post_returns_200(self, client):
        payload = build_post(title="Updated Title")
        response = client.put("/posts/1", payload)
        assert response.status_code == 200

    def test_delete_post_returns_200(self, client):
        response = client.delete("/posts/1")
        assert response.status_code == 200
