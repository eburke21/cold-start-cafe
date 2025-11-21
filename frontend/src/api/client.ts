/**
 * Typed API client for the ColdStart Café backend.
 *
 * Thin wrapper around fetch with error handling.
 * Base URL defaults to "/api/v1" (proxied by Vite in dev).
 */

import type { AddSignalRequest, AddSignalResponse, CreateSimulationResponse, GetSimulationResponse } from "../types/simulation.ts";
import type { MovieSearchResponse, MovieSearchResult } from "../types/movies.ts";

const BASE_URL = "/api/v1";

/** Structured error from the API */
export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // Response body may not be JSON
    }
    throw new ApiError(response.status, detail);
  }

  return response.json() as Promise<T>;
}

/** Create a new simulation session (step 0). */
export async function createSimulation(): Promise<CreateSimulationResponse> {
  return request<CreateSimulationResponse>("/simulation", { method: "POST" });
}

/** Add a signal and get the new step. */
export async function addSignal(
  sessionId: string,
  signal: AddSignalRequest,
): Promise<AddSignalResponse> {
  return request<AddSignalResponse>(`/simulation/${sessionId}/signal`, {
    method: "POST",
    body: JSON.stringify(signal),
  });
}

/** Get the full simulation state. */
export async function getSimulation(
  sessionId: string,
): Promise<GetSimulationResponse> {
  return request<GetSimulationResponse>(`/simulation/${sessionId}`);
}

/** Search movies by title substring. */
export async function searchMovies(
  query: string,
  limit: number = 10,
): Promise<MovieSearchResult[]> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  const data = await request<MovieSearchResponse>(
    `/movies/search?${params.toString()}`,
  );
  return data.results;
}
