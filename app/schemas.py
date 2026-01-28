from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=256)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PartOffer(BaseModel):
    supplier: str
    number: str
    name: str
    price: float
    currency: str = "RUB"
    qty: int
    delivery_days: int | None = None


class SearchResponse(BaseModel):
    number: str
    offers: list[PartOffer]

