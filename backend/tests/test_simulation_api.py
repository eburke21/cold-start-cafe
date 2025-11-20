"""Integration tests for the simulation API endpoints.

Tests the full flow: create simulation → add signals → get state,
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


class TestCreateSimulation:
    """Tests for POST /api/v1/simulation."""

    def test_create_returns_201(self, client):
        response = client.post("/api/v1/simulation")
        assert response.status_code == 201

    def test_create_returns_session_id(self, client):
        response = client.post("/api/v1/simulation")
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) == 36  # UUID format

    def test_create_returns_step_0(self, client):
        response = client.post("/api/v1/simulation")
        data = response.json()
        step = data["step"]
        assert step["step_number"] == 0
        assert step["signal_added"] is None

    def test_step_0_has_four_algorithm_results(self, client):
        response = client.post("/api/v1/simulation")
        data = response.json()
        results = data["step"]["results"]
        assert len(results) == 4
        algorithm_names = {r["algorithm"] for r in results}
        assert algorithm_names == {"popularity", "content_based", "collaborative", "hybrid"}

    def test_step_0_popularity_has_recommendations(self, client):
        response = client.post("/api/v1/simulation")
        results = response.json()["step"]["results"]
        pop_result = next(r for r in results if r["algorithm"] == "popularity")
        assert len(pop_result["recommendations"]) == 10

    def test_step_0_content_based_is_empty(self, client):
        response = client.post("/api/v1/simulation")
        results = response.json()["step"]["results"]
        cb_result = next(r for r in results if r["algorithm"] == "content_based")
        assert len(cb_result["recommendations"]) == 0

    def test_step_0_collaborative_is_empty(self, client):
        response = client.post("/api/v1/simulation")
        results = response.json()["step"]["results"]
        collab_result = next(r for r in results if r["algorithm"] == "collaborative")
        assert len(collab_result["recommendations"]) == 0

    def test_create_returns_genre_distribution(self, client):
        response = client.post("/api/v1/simulation")
        data = response.json()
        assert "ground_truth_genre_distribution" in data
        dist = data["ground_truth_genre_distribution"]
        assert isinstance(dist, dict)
        assert len(dist) > 0
        # All values should be between 0 and 1
        assert all(0 < v <= 1.0 for v in dist.values())

    def test_create_returns_narration(self, client):
        response = client.post("/api/v1/simulation")
        narration = response.json()["step"]["narration"]
        assert isinstance(narration, str)
        assert len(narration) > 0

    def test_create_returns_available_movies(self, client):
        response = client.post("/api/v1/simulation")
        data = response.json()
        assert "available_movies_sample" in data
        movies = data["available_movies_sample"]
        assert len(movies) > 0
        assert "movie_id" in movies[0]
        assert "title" in movies[0]


class TestAddSignal:
    """Tests for POST /api/v1/simulation/{session_id}/signal."""

    @pytest.fixture()
    def session_id(self, client):
        """Create a fresh simulation and return its session ID."""
        response = client.post("/api/v1/simulation")
        return response.json()["session_id"]

    def test_add_rating_returns_200(self, client, session_id):
        response = client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={"type": "rating", "payload": {"movie_id": 50, "score": 5.0}},
        )
        assert response.status_code == 200

    def test_add_rating_returns_step_1(self, client, session_id):
        response = client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={"type": "rating", "payload": {"movie_id": 50, "score": 5.0}},
        )
        step = response.json()["step"]
        assert step["step_number"] == 1
        assert step["signal_added"]["type"] == "rating"

    def test_content_based_changes_after_rating(self, client, session_id):
        response = client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={"type": "rating", "payload": {"movie_id": 50, "score": 5.0}},
        )
        results = response.json()["step"]["results"]
        cb_result = next(r for r in results if r["algorithm"] == "content_based")
        # Content-based should now have recommendations (was empty at step 0)
        assert len(cb_result["recommendations"]) > 0

    def test_add_demographics(self, client, session_id):
        response = client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={
                "type": "demographic",
                "payload": {"age": 25, "gender": "M", "occupation": "student"},
            },
        )
        assert response.status_code == 200
        step = response.json()["step"]
        assert step["signal_added"]["type"] == "demographic"

    def test_add_genre_preferences(self, client, session_id):
        response = client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={"type": "genre_preference", "payload": {"genres": ["Action", "Comedy"]}},
        )
        assert response.status_code == 200
        results = response.json()["step"]["results"]
        cb_result = next(r for r in results if r["algorithm"] == "content_based")
        # Content-based should produce results after genre prefs
        assert len(cb_result["recommendations"]) > 0

    def test_add_view_history(self, client, session_id):
        response = client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={"type": "view_history", "payload": {"movie_ids": [1, 2, 3]}},
        )
        assert response.status_code == 200
        results = response.json()["step"]["results"]
        cb_result = next(r for r in results if r["algorithm"] == "content_based")
        assert len(cb_result["recommendations"]) > 0

    def test_metrics_are_valid(self, client, session_id):
        """All metric values should be between 0 and 1."""
        response = client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={"type": "rating", "payload": {"movie_id": 50, "score": 5.0}},
        )
        for result in response.json()["step"]["results"]:
            assert 0.0 <= result["precision_at_10"] <= 1.0
            assert 0.0 <= result["recall_at_10"] <= 1.0
            assert 0.0 <= result["ndcg_at_10"] <= 1.0

    def test_recommendations_have_metadata(self, client, session_id):
        """Each recommendation should include movie title and genres."""
        response = client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={"type": "rating", "payload": {"movie_id": 50, "score": 5.0}},
        )
        results = response.json()["step"]["results"]
        pop_result = next(r for r in results if r["algorithm"] == "popularity")
        for rec in pop_result["recommendations"]:
            assert "movie_id" in rec
            assert "title" in rec
            assert "genres" in rec
            assert isinstance(rec["title"], str)
            assert len(rec["title"]) > 0


class TestGetSimulation:
    """Tests for GET /api/v1/simulation/{session_id}."""

    def test_get_returns_all_steps(self, client):
        # Create session
        create_resp = client.post("/api/v1/simulation")
        session_id = create_resp.json()["session_id"]

        # Add two signals
        client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={"type": "rating", "payload": {"movie_id": 50, "score": 5.0}},
        )
        client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={"type": "rating", "payload": {"movie_id": 1, "score": 4.0}},
        )

        # Get full state
        response = client.get(f"/api/v1/simulation/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["steps"]) == 3  # step 0 + 2 signals

    def test_get_returns_current_signals(self, client):
        create_resp = client.post("/api/v1/simulation")
        session_id = create_resp.json()["session_id"]

        client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={"type": "rating", "payload": {"movie_id": 50, "score": 5.0}},
        )
        client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={
                "type": "demographic",
                "payload": {"age": 25, "gender": "F", "occupation": "artist"},
            },
        )

        response = client.get(f"/api/v1/simulation/{session_id}")
        signals = response.json()["current_signals"]
        assert signals["ratings_count"] == 1
        assert signals["has_demographics"] is True
        assert signals["genre_preferences"] == []
        assert signals["view_history_count"] == 0

    def test_steps_are_in_order(self, client):
        create_resp = client.post("/api/v1/simulation")
        session_id = create_resp.json()["session_id"]

        client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={"type": "rating", "payload": {"movie_id": 50, "score": 5.0}},
        )
        client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={"type": "rating", "payload": {"movie_id": 1, "score": 4.0}},
        )

        response = client.get(f"/api/v1/simulation/{session_id}")
        steps = response.json()["steps"]
        step_numbers = [s["step_number"] for s in steps]
        assert step_numbers == [0, 1, 2]


class TestErrorHandling:
    """Tests for error responses."""

    def test_invalid_session_returns_404(self, client):
        response = client.get("/api/v1/simulation/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_invalid_uuid_format_returns_404(self, client):
        response = client.get("/api/v1/simulation/not-a-uuid")
        assert response.status_code == 404

    def test_invalid_signal_type_returns_422(self, client):
        create_resp = client.post("/api/v1/simulation")
        session_id = create_resp.json()["session_id"]

        response = client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={"type": "invalid_type", "payload": {}},
        )
        assert response.status_code == 422

    def test_rating_out_of_range_returns_400(self, client):
        create_resp = client.post("/api/v1/simulation")
        session_id = create_resp.json()["session_id"]

        response = client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={"type": "rating", "payload": {"movie_id": 50, "score": 6.0}},
        )
        assert response.status_code == 400
        assert "score" in response.json()["detail"].lower()

    def test_invalid_movie_id_returns_400(self, client):
        create_resp = client.post("/api/v1/simulation")
        session_id = create_resp.json()["session_id"]

        response = client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={"type": "rating", "payload": {"movie_id": 999999, "score": 5.0}},
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_invalid_genre_returns_400(self, client):
        create_resp = client.post("/api/v1/simulation")
        session_id = create_resp.json()["session_id"]

        response = client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={"type": "genre_preference", "payload": {"genres": ["NotAGenre"]}},
        )
        assert response.status_code == 400
        assert "unknown genres" in response.json()["detail"].lower()

    def test_signal_on_missing_session_returns_404(self, client):
        response = client.post(
            "/api/v1/simulation/00000000-0000-0000-0000-000000000000/signal",
            json={"type": "rating", "payload": {"movie_id": 50, "score": 5.0}},
        )
        assert response.status_code == 404

    def test_missing_payload_fields_returns_400(self, client):
        create_resp = client.post("/api/v1/simulation")
        session_id = create_resp.json()["session_id"]

        response = client.post(
            f"/api/v1/simulation/{session_id}/signal",
            json={"type": "rating", "payload": {"movie_id": 50}},
        )
        assert response.status_code == 400
        assert "score" in response.json()["detail"].lower()
