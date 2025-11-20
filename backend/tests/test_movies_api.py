"""Integration tests for the movie search API endpoint.

Tests GET /api/v1/movies/search with various queries and edge cases.
"""

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Create a test client with the app lifespan (loads data once)."""
    with TestClient(app) as c:
        yield c


class TestMovieSearch:
    """Tests for GET /api/v1/movies/search."""

    def test_search_star_wars(self, client):
        response = client.get("/api/v1/movies/search?q=star+wars")
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) >= 1
        titles = [r["title"] for r in results]
        assert any("Star Wars" in t for t in titles)

    def test_search_returns_movie_fields(self, client):
        response = client.get("/api/v1/movies/search?q=toy+story")
        results = response.json()["results"]
        assert len(results) >= 1
        movie = results[0]
        assert "movie_id" in movie
        assert "title" in movie
        assert "genres" in movie

    def test_search_with_limit(self, client):
        response = client.get("/api/v1/movies/search?q=the&limit=3")
        results = response.json()["results"]
        assert len(results) <= 3

    def test_search_case_insensitive(self, client):
        lower = client.get("/api/v1/movies/search?q=star+wars").json()["results"]
        upper = client.get("/api/v1/movies/search?q=STAR+WARS").json()["results"]
        assert len(lower) == len(upper)
        assert lower[0]["movie_id"] == upper[0]["movie_id"]

    def test_search_gibberish_returns_empty(self, client):
        response = client.get("/api/v1/movies/search?q=zzzzxyzzy123")
        results = response.json()["results"]
        assert results == []

    def test_search_empty_query_returns_empty(self, client):
        response = client.get("/api/v1/movies/search?q=")
        results = response.json()["results"]
        assert results == []

    def test_search_no_query_returns_empty(self, client):
        response = client.get("/api/v1/movies/search")
        assert response.status_code == 200
        results = response.json()["results"]
        assert results == []

    def test_search_default_limit_is_10(self, client):
        response = client.get("/api/v1/movies/search?q=the")
        results = response.json()["results"]
        assert len(results) <= 10

    def test_search_limit_max_is_50(self, client):
        response = client.get("/api/v1/movies/search?q=the&limit=100")
        assert response.status_code == 422  # Exceeds max limit validation
