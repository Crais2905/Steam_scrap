from typing import Optional, List

from pydantic import BaseModel, Field


class Review(BaseModel):
    text: str
    is_positive: bool
    posted_date: str
    playtime: Optional[str] = None


class GameDetails(BaseModel):
    app_id: str
    title: str
    url: str
    developer: str
    publisher: str
    release_date: str
    price: str
    short_description: str
    overall_review_summary: str
    reviews: List[Review] = Field(default_factory=list)


class SteamGame(BaseModel):
    app_id: int
    name: str
    url: str


class SteamSearchResponse(BaseModel):
    query: str
    results: list[SteamGame]