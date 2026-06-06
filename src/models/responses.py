"""Pydantic response models for the JSONPlaceholder API.

Each class describes the *contract* a response must satisfy: which fields are
present and what type each one is. Validating a response against one of these
models (`Post.model_validate(response.json())`) checks the whole shape in a
single call and raises a precise error when the API drifts — far stronger than
asserting individual keys exist.
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class _APIModel(BaseModel):
    """Shared base for every response model.

    The API speaks camelCase (`userId`, `postId`); Python prefers snake_case.
    Each field maps the two with `alias`, and `populate_by_name` additionally
    lets tests build a model using the readable snake_case name when needed.
    """

    model_config = ConfigDict(populate_by_name=True)


class Post(_APIModel):
    user_id: int = Field(alias="userId")
    id: int
    title: str
    body: str


class Comment(_APIModel):
    post_id: int = Field(alias="postId")
    id: int
    name: str
    email: EmailStr
    body: str


class Geo(_APIModel):
    lat: str
    lng: str


class Address(_APIModel):
    street: str
    suite: str
    city: str
    zipcode: str
    geo: Geo


class Company(_APIModel):
    name: str
    catch_phrase: str = Field(alias="catchPhrase")
    bs: str


class User(_APIModel):
    id: int
    name: str
    username: str
    email: EmailStr
    address: Address
    phone: str
    website: str
    company: Company
