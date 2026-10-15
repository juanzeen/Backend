from typing import TypedDict, Generic, TypeVar, Literal
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorMessage(BaseModel):
    message: str


class ResponseDict(TypedDict, Generic[T]):
    data: T
    message: str


class ErrorResponseDict(TypedDict):
    detail: ErrorMessage


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(10, gt=0, le=100)


class StatsFilters(BaseModel):
    stat: Literal["pts", "ast", "reb", "stl", "blk"] | None = None
    period: Literal["season", "career"] | None = "career"
    order: Literal["asc", "desc"] | None = None


class PaginationDetails(BaseModel):
    page: int
    limit: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginationResponse(BaseModel, Generic[T]):
    message: str
    data: list[T]
    pagination: PaginationDetails
