/** Mirrors backend Pydantic models for the challenge API. */

export interface ChallengeTargetUser {
  demographics: {
    age: number | null;
    gender: string | null;
    occupation: string | null;
  };
  seed_ratings: Array<{
    movie_id: number;
    title: string;
    genres: string;
    score: number | null;
  }>;
}

export interface ChallengeMovie {
  movie_id: number;
  title: string;
  genres: string;
  score: number | null;
}

export interface CreateChallengeResponse {
  session_id: string;
  target_user: ChallengeTargetUser;
  available_movies: ChallengeMovie[];
}

export interface MetricScores {
  precision_at_10: number;
  recall_at_10: number;
  ndcg_at_10: number;
}

export interface AlgorithmScore {
  algorithm: string;
  precision_at_10: number;
  ndcg_at_10: number;
}

export interface SubmitChallengeResponse {
  user_score: MetricScores;
  algorithm_scores: AlgorithmScore[];
  narration: string;
  ground_truth_favorites: ChallengeMovie[];
}
