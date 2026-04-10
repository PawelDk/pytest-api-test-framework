

class TestPostsRead:
    def test_get_all_posts_returns_200(self, client):
        response = client.get("/posts")
        assert response.status_code == 200
