"""Download MovieLens 100K and convert to Parquet format.

Usage:
    uv run python scripts/prepare_data.py              # download + convert
    uv run python scripts/prepare_data.py --validate   # also print row counts and samples
"""

import argparse
import io
import re
import zipfile
from pathlib import Path

import urllib.request

import pandas as pd

MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-100k.zip"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"

# MovieLens 100K genre columns in u.item (order matters)
GENRE_NAMES = [
    "unknown",
    "Action",
    "Adventure",
    "Animation",
    "Children's",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Fantasy",
    "Film-Noir",
    "Horror",
    "Musical",
    "Mystery",
    "Romance",
    "Sci-Fi",
    "Thriller",
    "War",
    "Western",
]


def download_movielens(force: bool = False) -> Path:
    """Download MovieLens 100K zip if not already present."""
    zip_path = RAW_DIR / "ml-100k.zip"
    if zip_path.exists() and not force:
        print(f"Zip already exists at {zip_path}, skipping download.")
        return zip_path

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading MovieLens 100K from {MOVIELENS_URL}...")
    urllib.request.urlretrieve(MOVIELENS_URL, zip_path)
    size_mb = zip_path.stat().st_size / 1024 / 1024
    print(f"Downloaded {size_mb:.1f} MB to {zip_path}")
    return zip_path


def extract_zip(zip_path: Path) -> dict[str, bytes]:
    """Extract the three core files from the zip into memory."""
    needed = {"ml-100k/u.data", "ml-100k/u.item", "ml-100k/u.user"}
    extracted = {}
    with zipfile.ZipFile(zip_path) as zf:
        for name in needed:
            extracted[name.split("/")[1]] = zf.read(name)
    return extracted


def build_movies_df(raw_bytes: bytes) -> pd.DataFrame:
    """Parse u.item into a movies DataFrame.

    u.item format (pipe-separated, ISO-8859-1):
        movie_id | title | release_date | video_release_date | imdb_url | genre1..genre19
    """
    columns = [
        "movie_id",
        "title",
        "release_date",
        "video_release_date",
        "imdb_url",
        *GENRE_NAMES,
    ]
    df = pd.read_csv(
        io.BytesIO(raw_bytes),
        sep="|",
        header=None,
        names=columns,
        encoding="ISO-8859-1",
    )

    # Build pipe-delimited genre string from binary columns
    def row_genres(row: pd.Series) -> str:
        return "|".join(g for g in GENRE_NAMES if row[g] == 1)

    df["genres"] = df.apply(row_genres, axis=1)

    # Extract year from title, e.g. "Toy Story (1995)" -> 1995
    def extract_year(title: str) -> int | None:
        match = re.search(r"\((\d{4})\)\s*$", str(title))
        return int(match.group(1)) if match else None

    df["year"] = df["title"].apply(extract_year).astype("Int64")

    # Keep only the columns we need
    return df[["movie_id", "title", "genres", "year"]].copy()


def build_ratings_df(raw_bytes: bytes) -> pd.DataFrame:
    """Parse u.data into a ratings DataFrame.

    u.data format (tab-separated):
        user_id    movie_id    rating    timestamp
    """
    df = pd.read_csv(
        io.BytesIO(raw_bytes),
        sep="\t",
        header=None,
        names=["user_id", "movie_id", "rating", "timestamp"],
    )
    df["rating"] = df["rating"].astype(float)
    return df


def build_users_df(raw_bytes: bytes) -> pd.DataFrame:
    """Parse u.user into a users DataFrame.

    u.user format (pipe-separated):
        user_id | age | gender | occupation | zip_code
    """
    df = pd.read_csv(
        io.BytesIO(raw_bytes),
        sep="|",
        header=None,
        names=["user_id", "age", "gender", "occupation", "zip_code"],
    )
    return df


def save_parquet(df: pd.DataFrame, name: str) -> Path:
    """Save a DataFrame as a Parquet file in the data directory."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{name}.parquet"
    df.to_parquet(path, index=False, engine="pyarrow")
    print(f"Saved {name}.parquet ({len(df)} rows, {path.stat().st_size / 1024:.0f} KB)")
    return path


def validate(movies: pd.DataFrame, ratings: pd.DataFrame, users: pd.DataFrame) -> None:
    """Print row counts, column info, and sample rows for validation."""
    print("\n" + "=" * 60)
    print("VALIDATION REPORT")
    print("=" * 60)

    for name, df in [("movies", movies), ("ratings", ratings), ("users", users)]:
        print(f"\n--- {name} ---")
        print(f"  Rows:    {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Dtypes:\n{df.dtypes.to_string()}")
        print(f"\n  Sample (first 3 rows):")
        print(df.head(3).to_string(index=False))
        print()

    # Sanity checks
    assert len(movies) > 1600, f"Expected 1600+ movies, got {len(movies)}"
    assert len(ratings) == 100000, f"Expected 100000 ratings, got {len(ratings)}"
    assert len(users) > 900, f"Expected 900+ users, got {len(users)}"
    assert "genres" in movies.columns, "movies missing 'genres' column"
    assert "year" in movies.columns, "movies missing 'year' column"

    # Check a known movie
    toy_story = movies[movies["movie_id"] == 1].iloc[0]
    assert "Toy Story" in toy_story["title"], f"Movie 1 should be Toy Story, got {toy_story['title']}"
    assert toy_story["year"] == 1995, f"Toy Story year should be 1995, got {toy_story['year']}"
    print("All validation checks passed.")


def main():
    parser = argparse.ArgumentParser(description="Prepare MovieLens 100K data")
    parser.add_argument("--validate", action="store_true", help="Print validation report")
    parser.add_argument("--force", action="store_true", help="Re-download even if zip exists")
    args = parser.parse_args()

    # Check if parquet files already exist
    parquet_files = [DATA_DIR / f"{name}.parquet" for name in ("movies", "ratings", "users")]
    if all(p.exists() for p in parquet_files) and not args.force:
        print("All Parquet files already exist. Use --force to regenerate.")
        if args.validate:
            movies = pd.read_parquet(DATA_DIR / "movies.parquet")
            ratings = pd.read_parquet(DATA_DIR / "ratings.parquet")
            users = pd.read_parquet(DATA_DIR / "users.parquet")
            validate(movies, ratings, users)
        return

    # Download and extract
    zip_path = download_movielens(force=args.force)
    raw_files = extract_zip(zip_path)

    # Build DataFrames
    movies = build_movies_df(raw_files["u.item"])
    ratings = build_ratings_df(raw_files["u.data"])
    users = build_users_df(raw_files["u.user"])

    # Save as Parquet
    save_parquet(movies, "movies")
    save_parquet(ratings, "ratings")
    save_parquet(users, "users")

    if args.validate:
        validate(movies, ratings, users)

    print("\nDone! Parquet files saved to data/")


if __name__ == "__main__":
    main()
