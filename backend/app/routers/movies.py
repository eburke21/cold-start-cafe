"""API routes for movie search.

GET /api/v1/movies/search?q={query}&limit={limit} — Search movie catalog
"""

from fastapi import APIRouter, Query, Request

from app.models.movies import MovieSearchResponse, MovieSearchResult

router = APIRouter(prefix="/api/v1", tags=["movies"])

# Maximum results the client can request
MAX_SEARCH_LIMIT = 50


@router.get(
    "/movies/search",
    response_model=MovieSearchResponse,
)
async def search_movies(
    request: Request,
    q: str = Query(default="", description="Search query (title substring)"),
    limit: int = Query(default=10, ge=1, le=MAX_SEARCH_LIMIT, description="Max results"),
):
    """Search the movie catalog by title substring.

    Returns matching movies sorted by title relevance. Used by the frontend
    for the movie search/rating modal.
    """
    data = request.app.state.data
    raw_results = data.search_movies(query=q, limit=limit)

    results = [
        MovieSearchResult(
            movie_id=int(r["movie_id"]),
            title=str(r["title"]),
            genres=str(r.get("genres", "")),
        )
        for r in raw_results
    ]

    return MovieSearchResponse(results=results)
