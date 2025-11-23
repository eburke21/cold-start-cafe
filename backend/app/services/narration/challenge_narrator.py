"""Challenge-specific narration via the Claude API.

Always LLM-generated (no templates) — too many outcome combinations
for pre-generation. Returns the full narration text (non-streaming)
since challenge results are a one-shot reveal, not a progressive stream.
"""

import structlog

from app.config import settings
from app.data.loader import DataStore
from app.models.challenge import AlgorithmScore, MetricScores
from app.models.simulation import Demographics, Rating

logger = structlog.get_logger()

CHALLENGE_SYSTEM_PROMPT = """\
You are the warm, knowledgeable narrator of ColdStart Café — an interactive \
educational tool that demonstrates the cold-start problem in recommendation systems.

A human just competed against four recommendation algorithms to predict what \
movies a target user would enjoy. Your job is to deliver the verdict in 2-3 \
concise sentences (under 80 words).

Use a warm, café-themed voice. Be encouraging but honest. \
If they beat collaborative filtering, that's impressive — mention it specifically. \
If they lost to the popularity baseline, gently roast them. \
Reference specific algorithm names and scores.

Do NOT use markdown, bullet points, or headers. Write in flowing prose — \
like a friendly barista announcing the results of a taste-test competition."""


def _build_challenge_prompt(
    demographics: Demographics,
    seed_ratings: list[Rating],
    user_picks: list[int],
    user_score: MetricScores,
    algo_scores: list[AlgorithmScore],
    data: DataStore,
) -> str:
    """Build the user prompt with challenge context."""
    # Demographics summary
    demo_parts = []
    if demographics.age:
        demo_parts.append(f"age {demographics.age}")
    if demographics.gender:
        demo_parts.append(demographics.gender)
    if demographics.occupation:
        demo_parts.append(demographics.occupation)
    demo_str = ", ".join(demo_parts) if demo_parts else "unknown demographics"

    # Seed ratings summary
    seed_parts = []
    for r in seed_ratings:
        movie = data.get_movie(r.movie_id)
        title = movie["title"] if movie else f"Movie #{r.movie_id}"
        seed_parts.append(f"{title} ({r.score}/5)")
    seed_str = ", ".join(seed_parts)

    # User picks summary
    pick_titles = []
    for mid in user_picks[:5]:  # Show first 5 to keep prompt reasonable
        movie = data.get_movie(mid)
        if movie:
            pick_titles.append(movie["title"])
    picks_str = ", ".join(pick_titles)
    if len(user_picks) > 5:
        picks_str += f" (and {len(user_picks) - 5} more)"

    # Algorithm comparison
    algo_lines = []
    beats = 0
    for score in algo_scores:
        won = user_score.precision_at_10 > score.precision_at_10
        if won:
            beats += 1
        result = "BEAT" if won else "LOST TO"
        algo_lines.append(
            f"  {score.algorithm}: P@10={score.precision_at_10:.3f}, "
            f"NDCG@10={score.ndcg_at_10:.3f} — Human {result}"
        )

    return f"""Challenge results:

Target user: {demo_str}
Seed ratings: {seed_str}

Human picks: {picks_str}
Human scores: P@10={user_score.precision_at_10:.3f}, \
R@10={user_score.recall_at_10:.3f}, NDCG@10={user_score.ndcg_at_10:.3f}

Algorithm scores:
{chr(10).join(algo_lines)}

The human beat {beats}/4 algorithms.

Give a 2-3 sentence café-themed verdict."""


async def generate_challenge_narration(
    demographics: Demographics,
    seed_ratings: list[Rating],
    user_picks: list[int],
    user_score: MetricScores,
    algo_scores: list[AlgorithmScore],
    data: DataStore,
) -> str:
    """Generate narration for challenge results using the Claude API.

    Unlike simulation narration (which streams via SSE), challenge narration
    is returned as a complete string because the results page loads all at once.

    Args:
        demographics: The target user's demographics.
        seed_ratings: The 3 seed ratings shown to the challenger.
        user_picks: The user's 10 movie picks.
        user_score: The user's computed metrics.
        algo_scores: Pre-computed algorithm scores.
        data: The DataStore for looking up movie titles.

    Returns:
        A narration string (LLM-generated or fallback).
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("No ANTHROPIC_API_KEY set, using fallback narration")
        return _fallback_narration(user_score, algo_scores)

    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        user_prompt = _build_challenge_prompt(
            demographics,
            seed_ratings,
            user_picks,
            user_score,
            algo_scores,
            data,
        )

        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            system=CHALLENGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        # Extract text from the response
        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text += block.text
        return text or _fallback_narration(user_score, algo_scores)

    except Exception as e:
        logger.error("Challenge narration failed", error=str(e))
        return _fallback_narration(user_score, algo_scores)


def _fallback_narration(
    user_score: MetricScores,
    algo_scores: list[AlgorithmScore],
) -> str:
    """Generate a generic fallback narration when the LLM is unavailable."""
    beats = sum(1 for s in algo_scores if user_score.precision_at_10 > s.precision_at_10)

    if beats == 4:
        return (
            f"Impressive! You beat all four algorithms with a precision of "
            f"{user_score.precision_at_10:.1%}. The machines have met their match today."
        )
    elif beats >= 2:
        return (
            f"Not bad! You outperformed {beats} out of 4 algorithms with a precision of "
            f"{user_score.precision_at_10:.1%}. A solid showing at the café."
        )
    elif beats == 1:
        return (
            f"You managed to beat one algorithm with a precision of "
            f"{user_score.precision_at_10:.1%}. The machines had the upper hand today, "
            f"but there's always a rematch."
        )
    else:
        return (
            f"The algorithms swept this round with your precision at "
            f"{user_score.precision_at_10:.1%}. Don't worry — even seasoned baristas "
            f"have off days. Try again with a fresh perspective!"
        )
