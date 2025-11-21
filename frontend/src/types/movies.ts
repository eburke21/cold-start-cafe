/** Mirrors backend Pydantic models for the movie search API. */

export interface MovieSearchResult {
  movie_id: number;
  title: string;
  genres: string;
}

export interface MovieSearchResponse {
  results: MovieSearchResult[];
}
