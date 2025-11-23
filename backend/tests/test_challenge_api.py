"""Integration tests for the challenge mode API endpoints.

Tests the full flow: create challenge → submit picks → get results,
including error handling for invalid inputs and missing sessions.
"""

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Create a test client with the app lifespan (loads data once)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def challenge_session(client):
    """Create a challenge session once for reuse across tests."""
    response = client.post("/api/v1/challenge")
    assert response.status_code == 201
    return response.json()


class TestCreateChallenge:
    """Tests for POST /api/v1/challenge."""

    def test_create_returns_201(self, client):
        response = client.post("/api/v1/challenge")
        assert response.status_code == 201

    def test_create_returns_session_id(self, client):
        response = client.post("/api/v1/challenge")
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) == 36  # UUID format

    def test_create_returns_target_user(self, challenge_session):
        target = challenge_session["target_user"]
        assert "demographics" in target
        assert "seed_ratings" in target

    def test_target_user_has_demographics(self, challenge_session):
        demographics = challenge_session["target_user"]["demographics"]
        # At least age should be set for MovieLens users
        assert demographics.get("age") is not None or demographics.get("gender") is not None

    def test_target_user_has_seed_ratings(self, challenge_session):
        seed_ratings = challenge_session["target_user"]["seed_ratings"]
        assert len(seed_ratings) == 3
        for rating in seed_ratings:
            assert "movie_id" in rating
            assert "title" in rating
            assert "score" in rating
            assert rating["score"] >= 4.0  # Only high-rated movies as seeds

    def test_seed_ratings_have_movie_metadata(self, challenge_session):
        seed_ratings = challenge_session["target_user"]["seed_ratings"]
        for rating in seed_ratings:
            assert rating["title"]  # Non-empty title
            assert "genres" in rating

    def test_create_returns_available_movies(self, challenge_session):
        movies = challenge_session["available_movies"]
        assert len(movies) == 50
        for movie in movies:
            assert "movie_id" in movie
            assert "title" in movie
            assert "genres" in movie


class TestSubmitChallenge:
    """Tests for POST /api/v1/challenge/{session_id}/submit."""

    def test_submit_returns_200(self, client, challenge_session):
        session_id = challenge_session["session_id"]
        # Get 10 valid movie IDs from the available movies
        movies = challenge_session["available_movies"]
        picks = [m["movie_id"] for m in movies[:10]]

        response = client.post(
            f"/api/v1/challenge/{session_id}/submit",
            json={"picks": picks},
        )
        assert response.status_code == 200

    def test_submit_returns_user_scores(self, client):
        # Create a fresh challenge for this test
        create_resp = client.post("/api/v1/challenge")
        data = create_resp.json()
        session_id = data["session_id"]
        picks = [m["movie_id"] for m in data["available_movies"][:10]]

        response = client.post(
            f"/api/v1/challenge/{session_id}/submit",
            json={"picks": picks},
        )
        result = response.json()

        assert "user_score" in result
        user_score = result["user_score"]
        assert "precision_at_10" in user_score
        assert "recall_at_10" in user_score
        assert "ndcg_at_10" in user_score
        assert 0.0 <= user_score["precision_at_10"] <= 1.0
        assert 0.0 <= user_score["recall_at_10"] <= 1.0
        assert 0.0 <= user_score["ndcg_at_10"] <= 1.0

    def test_submit_returns_algorithm_scores(self, client):
        create_resp = client.post("/api/v1/challenge")
        data = create_resp.json()
        session_id = data["session_id"]
        picks = [m["movie_id"] for m in data["available_movies"][:10]]

        response = client.post(
            f"/api/v1/challenge/{session_id}/submit",
            json={"picks": picks},
        )
        result = response.json()

        assert "algorithm_scores" in result
        algo_scores = result["algorithm_scores"]
        assert len(algo_scores) == 4
        algo_names = {s["algorithm"] for s in algo_scores}
        assert algo_names == {"popularity", "content_based", "collaborative", "hybrid"}

        for score in algo_scores:
            assert 0.0 <= score["precision_at_10"] <= 1.0
            assert 0.0 <= score["ndcg_at_10"] <= 1.0

    def test_submit_returns_narration(self, client):
        create_resp = client.post("/api/v1/challenge")
        data = create_resp.json()
        session_id = data["session_id"]
        picks = [m["movie_id"] for m in data["available_movies"][:10]]

        response = client.post(
            f"/api/v1/challenge/{session_id}/submit",
            json={"picks": picks},
        )
        result = response.json()

        assert "narration" in result
        assert len(result["narration"]) > 0  # Non-empty narration

    def test_submit_returns_ground_truth_favorites(self, client):
        create_resp = client.post("/api/v1/challenge")
        data = create_resp.json()
        session_id = data["session_id"]
        picks = [m["movie_id"] for m in data["available_movies"][:10]]

        response = client.post(
            f"/api/v1/challenge/{session_id}/submit",
            json={"picks": picks},
        )
        result = response.json()

        assert "ground_truth_favorites" in result
        favorites = result["ground_truth_favorites"]
        assert len(favorites) > 0
        assert len(favorites) <= 10
        for fav in favorites:
            assert "movie_id" in fav
            assert "title" in fav
            assert "score" in fav
            assert fav["score"] >= 4.0  # Only top-rated movies


class TestChallengeErrors:
    """Tests for challenge error handling."""

    def test_submit_less_than_10_picks(self, client):
        create_resp = client.post("/api/v1/challenge")
        data = create_resp.json()
        session_id = data["session_id"]
        picks = [m["movie_id"] for m in data["available_movies"][:5]]

        response = client.post(
            f"/api/v1/challenge/{session_id}/submit",
            json={"picks": picks},
        )
        assert response.status_code == 422  # Pydantic validation (min_length=10)

    def test_submit_more_than_10_picks(self, client):
        create_resp = client.post("/api/v1/challenge")
        data = create_resp.json()
        session_id = data["session_id"]
        picks = [m["movie_id"] for m in data["available_movies"][:15]]

        response = client.post(
            f"/api/v1/challenge/{session_id}/submit",
            json={"picks": picks},
        )
        assert response.status_code == 422  # Pydantic validation (max_length=10)

    def test_submit_duplicate_movie_ids(self, client):
        create_resp = client.post("/api/v1/challenge")
        data = create_resp.json()
        session_id = data["session_id"]
        movie_id = data["available_movies"][0]["movie_id"]
        picks = [movie_id] * 10  # All duplicates

        response = client.post(
            f"/api/v1/challenge/{session_id}/submit",
            json={"picks": picks},
        )
        assert response.status_code == 400
        assert "Duplicate" in response.json()["detail"]

    def test_submit_invalid_session(self, client):
        response = client.post(
            "/api/v1/challenge/00000000-0000-0000-0000-000000000000/submit",
            json={"picks": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
        )
        assert response.status_code == 404

    def test_submit_invalid_uuid_format(self, client):
        response = client.post(
            "/api/v1/challenge/not-a-uuid/submit",
            json={"picks": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
        )
        assert response.status_code == 404

    def test_submit_invalid_movie_id(self, client):
        create_resp = client.post("/api/v1/challenge")
        data = create_resp.json()
        session_id = data["session_id"]
        valid_picks = [m["movie_id"] for m in data["available_movies"][:9]]
        picks = valid_picks + [999999]  # Invalid movie ID

        response = client.post(
            f"/api/v1/challenge/{session_id}/submit",
            json={"picks": picks},
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]
