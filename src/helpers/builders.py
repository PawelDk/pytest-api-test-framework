# Request payload builders. Keys use the API's camelCase wire format (userId, postId).
def build_post(title: str = "Test Post", body: str = "Test body content", user_id: int = 1) -> dict:
    return {"title": title, "body": body, "userId": user_id}


def build_comment(post_id: int = 1, name: str = "Test Comment", email: str = "test@example.com",
                  body: str = "Comment body") -> dict:
    return {"postId": post_id, "name": name, "email": email, "body": body}
