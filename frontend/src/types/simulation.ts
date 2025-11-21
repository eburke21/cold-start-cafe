/** Mirrors backend Pydantic models for the simulation API. */

export type SignalType =
  | "rating"
  | "demographic"
  | "genre_preference"
  | "view_history";

export type AlgorithmName =
  | "popularity"
  | "content_based"
  | "collaborative"
  | "hybrid";

export interface Rating {
  movie_id: number;
  score: number;
}

export interface Demographics {
  age: number | null;
  gender: string | null;
  occupation: string | null;
}

export interface Signal {
  type: SignalType;
  step: number;
  payload: Record<string, unknown>;
}

export interface MovieRecommendation {
  movie_id: number;
  title: string;
  genres: string;
  score: number | null;
}

export interface AlgorithmResult {
  algorithm: AlgorithmName;
  recommendations: MovieRecommendation[];
  precision_at_10: number;
  recall_at_10: number;
  ndcg_at_10: number;
}

export interface SimulationStep {
  step_number: number;
  signal_added: Signal | null;
  results: AlgorithmResult[];
  narration: string;
}

export interface CurrentSignals {
  ratings_count: number;
  has_demographics: boolean;
  genre_preferences: string[];
  view_history_count: number;
}

/** POST /api/v1/simulation response */
export interface CreateSimulationResponse {
  session_id: string;
  ground_truth_genre_distribution: Record<string, number>;
  step: SimulationStep;
  available_movies_sample: MovieRecommendation[];
}

/** POST /api/v1/simulation/{id}/signal request */
export interface AddSignalRequest {
  type: SignalType;
  payload: Record<string, unknown>;
}

/** POST /api/v1/simulation/{id}/signal response */
export interface AddSignalResponse {
  step: SimulationStep;
}

/** GET /api/v1/simulation/{id} response */
export interface GetSimulationResponse {
  session_id: string;
  steps: SimulationStep[];
  current_signals: CurrentSignals;
}
