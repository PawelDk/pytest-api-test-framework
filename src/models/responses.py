"""Pydantic response models for the JSONPlaceholder API.

Each class defines the contract a response must satisfy: which fields are
present and their types.
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class _APIModel(BaseModel):
    """Shared base. Fields map the API's camelCase to snake_case via `alias`;
    `populate_by_name` also lets tests build models by the snake_case name."""

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
