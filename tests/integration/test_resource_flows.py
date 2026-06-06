"""Integration tests for cross-resource relationships.

Unlike the component tests, these chain several endpoints in one flow — e.g.
fetch a user, then their posts — to verify the links between resources hold.
"""

import pytest
from pydantic import TypeAdapter

from src.helpers.builders import build_comment, build_post
from src.models.responses import Comment, Post, User

# Every test in this module hits the real API.
pytestmark = pytest.mark.live

PostList = TypeAdapter(list[Post])
CommentList = TypeAdapter(list[Comment])


class TestUserPostsRelationship:
    """Posts returned for a user belong to that user."""

    def test_posts_belong_to_fetched_user(self, client):
        user_response = client.get("/users/1")
        assert user_response.status_code == 200
        user = User.model_validate(user_response.json())

        posts_response = client.get(f"/posts?userId={user.id}")
        assert posts_response.status_code == 200

        posts = PostList.validate_python(posts_response.json())
        assert len(posts) > 0
        assert all(post.user_id == user.id for post in posts)

    @pytest.mark.parametrize("user_id", [1, 2, 3])
    def test_multiple_users_all_have_posts(self, client, user_id):
        response = client.get(f"/posts?userId={user_id}")
        assert response.status_code == 200

        posts = PostList.validate_python(response.json())
        assert len(posts) > 0
        assert all(post.user_id == user_id for post in posts)

    def test_user_must_exist_before_fetching_their_posts(self, client):
        user_response = client.get("/users/1")
        assert user_response.status_code == 200, "User not found — skipping posts fetch"
        user_id = user_response.json()["id"]

        posts_response = client.get(f"/posts?userId={user_id}")
        assert posts_response.status_code == 200
        assert len(posts_response.json()) > 0


class TestPostCommentsRelationship:
    """Comments returned for a post reference that post."""

    def test_comments_reference_their_post(self, client):
        post_response = client.get("/posts/1")
        assert post_response.status_code == 200
        post = Post.model_validate(post_response.json())

        comments_response = client.get(f"/posts/{post.id}/comments")
        assert comments_response.status_code == 200

        comments = CommentList.validate_python(comments_response.json())
        assert len(comments) > 0
        assert all(comment.post_id == post.id for comment in comments)

    def test_created_post_comments_endpoint_is_reachable(self, client):
        payload = build_post(title="Integration Test Post", user_id=1)

        post_response = client.post("/posts", payload)
        assert post_response.status_code == 201
        post_id = post_response.json()["id"]

        comments_response = client.get(f"/posts/{post_id}/comments")
        assert comments_response.status_code == 200


class TestPostCommentCreation:
    """Creating a comment round-trips through the API contract."""

    def test_create_comment_then_fetch_comments_list(self, client):
        payload = build_comment(post_id=1, name="Flow Test Comment", email="flow@example.com", body="Testing the chain")

        post_response = client.post("/posts/1/comments", payload)
        assert post_response.status_code == 201

        get_response = client.get("/posts/1/comments")
        assert get_response.status_code == 200
        comments = CommentList.validate_python(get_response.json())
        assert len(comments) > 0

    def test_create_post_then_comment_reflects_sent_data(self, client):
        post_payload = build_post(title="Post for Comment Test", user_id=1)
        post_response = client.post("/posts", post_payload)
        assert post_response.status_code == 201
        post = Post.model_validate(post_response.json())

        comment_payload = build_comment(post_id=post.id, name="Integration Comment", email="test@example.com", body="Comment body")
        comment_response = client.post(f"/posts/{post.id}/comments", comment_payload)
        assert comment_response.status_code == 201

        comment = Comment.model_validate(comment_response.json())
        assert comment.name == comment_payload["name"]
        assert comment.email == comment_payload["email"]
        assert comment.body == comment_payload["body"]
        assert comment.post_id == post.id