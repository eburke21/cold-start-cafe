/**
 * Custom hook that encapsulates all simulation state and API calls.
 *
 * Single source of truth for the simulation — components receive
 * data and callbacks from this hook, never call the API directly.
 */

import { useCallback, useState } from "react";
import * as api from "../api/client.ts";
import type { ApiError } from "../api/client.ts";
import type {
  Demographics,
  MovieRecommendation,
  SimulationStep,
} from "../types/simulation.ts";

export interface SimulationState {
  sessionId: string | null;
  steps: SimulationStep[];
  genreDistribution: Record<string, number>;
  availableMovies: MovieRecommendation[];
  ratingsCount: number;
  hasDemographics: boolean;
  genrePreferences: string[];
  viewHistoryCount: number;
  isLoading: boolean;
  error: string | null;
}

export interface SimulationActions {
  createSimulation: () => Promise<void>;
  addRating: (movieId: number, score: number) => Promise<void>;
  setDemographics: (demographics: Demographics) => Promise<void>;
  setGenrePreferences: (genres: string[]) => Promise<void>;
  addViewHistory: (movieIds: number[]) => Promise<void>;
  reset: () => void;
}

const initialState: SimulationState = {
  sessionId: null,
  steps: [],
  genreDistribution: {},
  availableMovies: [],
  ratingsCount: 0,
  hasDemographics: false,
  genrePreferences: [],
  viewHistoryCount: 0,
  isLoading: false,
  error: null,
};

export function useSimulation(): SimulationState & SimulationActions {
  const [state, setState] = useState<SimulationState>(initialState);

  const createSimulation = useCallback(async () => {
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const data = await api.createSimulation();
      setState({
        sessionId: data.session_id,
        steps: [data.step],
        genreDistribution: data.ground_truth_genre_distribution,
        availableMovies: data.available_movies_sample,
        ratingsCount: 0,
        hasDemographics: false,
        genrePreferences: [],
        viewHistoryCount: 0,
        isLoading: false,
        error: null,
      });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to create simulation";
      setState((s) => ({ ...s, isLoading: false, error: message }));
    }
  }, []);

  const addRating = useCallback(
    async (movieId: number, score: number) => {
      if (!state.sessionId) return;
      setState((s) => ({ ...s, isLoading: true, error: null }));
      try {
        const data = await api.addSignal(state.sessionId, {
          type: "rating",
          payload: { movie_id: movieId, score },
        });
        setState((s) => ({
          ...s,
          steps: [...s.steps, data.step],
          ratingsCount: s.ratingsCount + 1,
          isLoading: false,
        }));
      } catch (err) {
        const message =
          (err as ApiError).detail || "Failed to add rating";
        setState((s) => ({ ...s, isLoading: false, error: message }));
      }
    },
    [state.sessionId],
  );

  const setDemographics = useCallback(
    async (demographics: Demographics) => {
      if (!state.sessionId) return;
      setState((s) => ({ ...s, isLoading: true, error: null }));
      try {
        const data = await api.addSignal(state.sessionId, {
          type: "demographic",
          payload: demographics as unknown as Record<string, unknown>,
        });
        setState((s) => ({
          ...s,
          steps: [...s.steps, data.step],
          hasDemographics: true,
          isLoading: false,
        }));
      } catch (err) {
        const message =
          (err as ApiError).detail || "Failed to set demographics";
        setState((s) => ({ ...s, isLoading: false, error: message }));
      }
    },
    [state.sessionId],
  );

  const setGenrePreferences = useCallback(
    async (genres: string[]) => {
      if (!state.sessionId) return;
      setState((s) => ({ ...s, isLoading: true, error: null }));
      try {
        const data = await api.addSignal(state.sessionId, {
          type: "genre_preference",
          payload: { genres },
        });
        setState((s) => ({
          ...s,
          steps: [...s.steps, data.step],
          genrePreferences: genres,
          isLoading: false,
        }));
      } catch (err) {
        const message =
          (err as ApiError).detail || "Failed to set genre preferences";
        setState((s) => ({ ...s, isLoading: false, error: message }));
      }
    },
    [state.sessionId],
  );

  const addViewHistory = useCallback(
    async (movieIds: number[]) => {
      if (!state.sessionId) return;
      setState((s) => ({ ...s, isLoading: true, error: null }));
      try {
        const data = await api.addSignal(state.sessionId, {
          type: "view_history",
          payload: { movie_ids: movieIds },
        });
        setState((s) => ({
          ...s,
          steps: [...s.steps, data.step],
          viewHistoryCount: s.viewHistoryCount + movieIds.length,
          isLoading: false,
        }));
      } catch (err) {
        const message =
          (err as ApiError).detail || "Failed to add view history";
        setState((s) => ({ ...s, isLoading: false, error: message }));
      }
    },
    [state.sessionId],
  );

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  return {
    ...state,
    createSimulation,
    addRating,
    setDemographics,
    setGenrePreferences,
    addViewHistory,
    reset,
  };
}
