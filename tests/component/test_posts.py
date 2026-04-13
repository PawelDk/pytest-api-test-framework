import pytest
from src.helpers.builders import build_post


class TestPostsRead:
    def test_get_all_posts_returns_200(self, client):
        response = client.get("/posts")
        assert response.status_code == 200

    def test_get_all_posts_returns_list(self, client):
        response = client.get("/posts")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_single_post_returns_200(self, client):
        response = client.get("/posts/1")
        assert response.status_code == 200

    def test_get_single_post_has_expected_fields(self, client):
        response = client.get("/posts/1")
        data = response.json()
        assert "id" in data
        assert "title" in data
        assert "body" in data
        assert "userId" in data

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
        data = response.json()
        assert data["title"] == "Specific Title"
        assert data["body"] == "Specific Body"
        assert data["userId"] == 3

    def test_update_post_returns_200(self, client):
        payload = build_post(title="Updated Title")
        response = client.put("/posts/1", payload)
        assert response.status_code == 200

    def test_delete_post_returns_200(self, client):
        response = client.delete("/posts/1")
        assert response.status_code == 200
