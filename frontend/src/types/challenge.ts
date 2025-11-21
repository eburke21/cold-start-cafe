/** Mirrors backend Pydantic models for the challenge API. (Placeholder for Phase 6+) */

export interface ChallengeTargetUser {
  demographics: {
    age: number;
    gender: string;
    occupation: string;
  };
  seed_ratings: Array<{
    movie_id: number;
    title: string;
    score: number;
  }>;
}

export interface CreateChallengeResponse {
  session_id: string;
  target_user: ChallengeTargetUser;
  available_movies: Array<{
    movie_id: number;
    title: string;
    genres: string;
  }>;
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
  ground_truth_favorites: Array<{
    movie_id: number;
    title: string;
    score: number;
  }>;
}
