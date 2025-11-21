"""Ground-truth user selection and relevant-set extraction.

Each simulation session uses a real MovieLens user as hidden ground truth.
The user's high-rated movies (≥ 4.0) form the "relevant set" that metrics
are evaluated against. The algorithms never see these ratings — only the
simulated user's added signals.
"""

import random

from app.data.loader import DataStore


class GroundTruthUser:
    """Holds ground-truth data for a single simulation session.

    Attributes:
        user_id: The real MovieLens user ID selected as ground truth.
        relevant_movie_ids: Set of movie IDs the user rated 4.0 or higher.
        all_rated_movie_ids: Set of all movie IDs the user has rated.
    """

    def __init__(self, user_id: int, relevant_movie_ids: set[int], all_rated_movie_ids: set[int]):
        self.user_id = user_id
        self.relevant_movie_ids = relevant_movie_ids
        self.all_rated_movie_ids = all_rated_movie_ids


def select_ground_truth_user(data: DataStore, rng: random.Random | None = None) -> GroundTruthUser:
    """Select a random eligible user and extract their ground-truth data.

    Args:
        data: The DataStore with MovieLens data loaded.
        rng: Optional Random instance for reproducible selection. If None,
             uses the default random module.

    Returns:
        A GroundTruthUser with the relevant set (movies rated ≥ 4.0) and
        full set of rated movie IDs.
    """
    eligible = data.get_eligible_ground_truth_users()
    if not eligible:
        raise ValueError("No eligible ground-truth users found in dataset")

    if rng is not None:
        user_id = rng.choice(eligible)
    else:
        user_id = random.choice(eligible)

    # Get all ratings for this user
    user_ratings = data.ratings_df[data.ratings_df["user_id"] == user_id]

    # Relevant set: movies rated 4.0 or higher
    relevant = set(user_ratings[user_ratings["rating"] >= 4.0]["movie_id"].tolist())

    # All rated movies (used to exclude from recommendations)
    all_rated = set(user_ratings["movie_id"].tolist())

    return GroundTruthUser(
        user_id=user_id,
        relevant_movie_ids=relevant,
        all_rated_movie_ids=all_rated,
    )
