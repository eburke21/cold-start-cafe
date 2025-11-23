/**
 * Custom hook that encapsulates all challenge mode state and API calls.
 *
 * Manages the three-phase state machine: setup → picking → results.
 * Components receive data and callbacks from this hook, never call
 * the API directly (same pattern as useSimulation).
 */

import { useCallback, useState } from "react";
import * as api from "../api/client.ts";
import type { ApiError } from "../api/client.ts";
import type {
  AlgorithmScore,
  ChallengeMovie,
  ChallengeTargetUser,
  MetricScores,
  SubmitChallengeResponse,
} from "../types/challenge.ts";

export type ChallengePhase = "setup" | "picking" | "results";

export interface ChallengeState {
  phase: ChallengePhase;
  sessionId: string | null;
  targetUser: ChallengeTargetUser | null;
  availableMovies: ChallengeMovie[];
  picks: number[];
  userScore: MetricScores | null;
  algoScores: AlgorithmScore[];
  narration: string;
  groundTruthFavorites: ChallengeMovie[];
  isLoading: boolean;
  error: string | null;
}

export interface ChallengeActions {
  createChallenge: () => Promise<void>;
  startPicking: () => void;
  togglePick: (movieId: number) => void;
  removePick: (movieId: number) => void;
  submitPicks: () => Promise<void>;
  tryAgain: () => Promise<void>;
}

const initialState: ChallengeState = {
  phase: "setup",
  sessionId: null,
  targetUser: null,
  availableMovies: [],
  picks: [],
  userScore: null,
  algoScores: [],
  narration: "",
  groundTruthFavorites: [],
  isLoading: false,
  error: null,
};

export function useChallenge(): ChallengeState & ChallengeActions {
  const [state, setState] = useState<ChallengeState>(initialState);

  const createChallenge = useCallback(async () => {
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const data = await api.createChallenge();
      setState({
        ...initialState,
        phase: "setup",
        sessionId: data.session_id,
        targetUser: data.target_user,
        availableMovies: data.available_movies,
        isLoading: false,
      });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to create challenge";
      setState((s) => ({ ...s, isLoading: false, error: message }));
    }
  }, []);

  const startPicking = useCallback(() => {
    setState((s) => ({ ...s, phase: "picking" }));
  }, []);

  const togglePick = useCallback((movieId: number) => {
    setState((s) => {
      const idx = s.picks.indexOf(movieId);
      if (idx >= 0) {
        // Remove
        return { ...s, picks: s.picks.filter((id) => id !== movieId) };
      }
      if (s.picks.length >= 10) {
        // Max 10 picks
        return s;
      }
      return { ...s, picks: [...s.picks, movieId] };
    });
  }, []);

  const removePick = useCallback((movieId: number) => {
    setState((s) => ({
      ...s,
      picks: s.picks.filter((id) => id !== movieId),
    }));
  }, []);

  const submitPicks = useCallback(async () => {
    if (!state.sessionId || state.picks.length !== 10) return;
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const result: SubmitChallengeResponse = await api.submitChallenge(
        state.sessionId,
        state.picks,
      );
      setState((s) => ({
        ...s,
        phase: "results",
        userScore: result.user_score,
        algoScores: result.algorithm_scores,
        narration: result.narration,
        groundTruthFavorites: result.ground_truth_favorites,
        isLoading: false,
      }));
    } catch (err) {
      const message =
        (err as ApiError).detail || "Failed to submit challenge";
      setState((s) => ({ ...s, isLoading: false, error: message }));
    }
  }, [state.sessionId, state.picks]);

  const tryAgain = useCallback(async () => {
    setState({ ...initialState, isLoading: true });
    try {
      const data = await api.createChallenge();
      setState({
        ...initialState,
        phase: "setup",
        sessionId: data.session_id,
        targetUser: data.target_user,
        availableMovies: data.available_movies,
        isLoading: false,
      });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to create challenge";
      setState((s) => ({ ...s, isLoading: false, error: message }));
    }
  }, []);

  return {
    ...state,
    createChallenge,
    startPicking,
    togglePick,
    removePick,
    submitPicks,
    tryAgain,
  };
}
