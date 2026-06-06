"""Unit tests proving the response models reject malformed data.

The component/integration tests only ever feed the models *good* live data,
so they show the happy path. These feed *bad* data and assert the model
raises — proving the schema is a real guardian, not decoration. Fully offline.
"""

import pytest
from pydantic import TypeAdapter, ValidationError

from src.models.responses import Comment, Post


def _valid_post() -> dict:
    return {"userId": 1, "id": 1, "title": "t", "body": "b"}


class TestSchemaRejectsBadData:
    def test_wrong_type_is_rejected(self):
        """A non-numeric id must fail — a plain `"id" in data` check would pass."""
        bad = _valid_post() | {"id": "abc"}
        with pytest.raises(ValidationError):
            Post.model_validate(bad)

    def test_missing_required_field_is_rejected(self):
        bad = _valid_post()
        del bad["title"]
        with pytest.raises(ValidationError):
            Post.model_validate(bad)

    def test_malformed_email_is_rejected(self):
        """EmailStr validates format, not just presence."""
        bad = {"postId": 1, "id": 1, "name": "n", "email": "not-an-email", "body": "b"}
        with pytest.raises(ValidationError):
            Comment.model_validate(bad)

    def test_list_validation_pinpoints_the_bad_element(self):
        """TypeAdapter reports which index broke the contract."""
        items = [_valid_post(), _valid_post() | {"id": "abc"}]
        with pytest.raises(ValidationError) as exc:
            TypeAdapter(list[Post]).validate_python(items)
        assert "1" in str(exc.value)  # the second element (index 1) is the offender