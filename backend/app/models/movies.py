"""Pydantic models for the movie search API endpoint."""

from pydantic import BaseModel


class MovieSearchResult(BaseModel):
    """A single movie in search results."""

    movie_id: int
    title: str
    genres: str


class MovieSearchResponse(BaseModel):
    """Response for GET /api/v1/movies/search."""

    results: list[MovieSearchResult]
