/**
 * Movie picking interface for challenge mode.
 *
 * Full-width movie browser with search bar and a scrollable grid of movie
 * cards. Each card shows title, genres, and a select/deselect button.
 * Selected movies appear as removable chips above the grid.
 * "Submit Picks" button enabled at exactly 10 selections.
 */

import { useEffect, useState } from "react";
import {
  Badge,
  Box,
  Button,
  Flex,
  Grid,
  HStack,
  Input,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react";

import * as api from "../api/client";
import type { ChallengeMovie } from "../types/challenge";
import type { MovieSearchResult } from "../types/movies";

interface MoviePickerProps {
  availableMovies: ChallengeMovie[];
  picks: number[];
  onTogglePick: (movieId: number) => void;
  onRemovePick: (movieId: number) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

export default function MoviePicker({
  availableMovies,
  picks,
  onTogglePick,
  onRemovePick,
  onSubmit,
  isLoading,
}: MoviePickerProps) {
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<MovieSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const movies = await api.searchMovies(query, 30);
        setSearchResults(movies);
      } catch {
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Show search results when searching, otherwise show available movies
  const displayMovies: Array<{ movie_id: number; title: string; genres: string }> =
    query.trim() && searchResults.length > 0
      ? searchResults
      : availableMovies;

  // Map of picked movie IDs for O(1) lookup
  const pickedSet = new Set(picks);

  // Get title for a picked movie
  const getPickTitle = (movieId: number): string => {
    const fromAvailable = availableMovies.find((m) => m.movie_id === movieId);
    if (fromAvailable) return fromAvailable.title;
    const fromSearch = searchResults.find((m) => m.movie_id === movieId);
    if (fromSearch) return fromSearch.title;
    return `Movie #${movieId}`;
  };

  return (
    <VStack gap={4} align="stretch">
      {/* Pick counter and submit button */}
      <Flex justify="space-between" align="center">
        <HStack gap={2}>
          <Text fontSize="lg" fontWeight="bold" color="brand.espresso">
            🎬 Pick 10 Movies
          </Text>
          <Badge
            bg={picks.length === 10 ? "green.500" : "brand.honey"}
            color={picks.length === 10 ? "white" : "brand.espresso"}
            fontSize="sm"
            px={2}
            borderRadius="full"
          >
            {picks.length}/10
          </Badge>
        </HStack>
        <Button
          bg="brand.terracotta"
          color="white"
          _hover={{ bg: "brand.terracottaDark" }}
          onClick={onSubmit}
          disabled={picks.length !== 10 || isLoading}
          size="sm"
        >
          {isLoading ? <Spinner size="xs" mr={2} /> : null}
          Submit Picks
        </Button>
      </Flex>

      {/* Selected movies chips */}
      {picks.length > 0 && (
        <Flex wrap="wrap" gap={2}>
          {picks.map((movieId) => (
            <Badge
              key={movieId}
              bg="brand.linenDark"
              color="brand.espresso"
              px={2}
              py={1}
              borderRadius="full"
              cursor="pointer"
              _hover={{ bg: "brand.terracottaLight", color: "white" }}
              onClick={() => onRemovePick(movieId)}
            >
              {getPickTitle(movieId)} ✕
            </Badge>
          ))}
        </Flex>
      )}

      {/* Search input */}
      <Input
        placeholder="Search movies by title..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        bg="white"
        borderColor="brand.linenDark"
        _focus={{ borderColor: "brand.teal" }}
        aria-label="Search movies by title"
      />

      {isSearching && (
        <Flex justify="center" py={4}>
          <Spinner size="sm" color="brand.teal" />
        </Flex>
      )}

      {/* Movie grid */}
      <Box maxH="500px" overflowY="auto" pr={2}>
        {displayMovies.length === 0 && query.trim() && !isSearching && (
          <Text color="brand.espressoLight" textAlign="center" py={4}>
            No movies found matching &ldquo;{query}&rdquo;
          </Text>
        )}

        <Grid templateColumns="repeat(2, 1fr)" gap={3}>
          {displayMovies.map((movie) => {
            const isPicked = pickedSet.has(movie.movie_id);
            return (
              <Box
                key={movie.movie_id}
                p={3}
                bg={isPicked ? "brand.honeyLight" : "white"}
                borderRadius="lg"
                shadow="sm"
                borderWidth="2px"
                borderColor={isPicked ? "brand.honey" : "transparent"}
                cursor={
                  isPicked || picks.length < 10 ? "pointer" : "not-allowed"
                }
                opacity={!isPicked && picks.length >= 10 ? 0.5 : 1}
                _hover={
                  isPicked || picks.length < 10
                    ? { shadow: "md", borderColor: "brand.teal" }
                    : undefined
                }
                transition="all 0.15s ease"
                role="button"
                tabIndex={isPicked || picks.length < 10 ? 0 : -1}
                aria-pressed={isPicked}
                aria-label={`${isPicked ? "Remove" : "Select"} ${movie.title}`}
                onClick={() => {
                  if (isPicked || picks.length < 10) {
                    onTogglePick(movie.movie_id);
                  }
                }}
                onKeyDown={(e) => {
                  if (
                    (e.key === "Enter" || e.key === " ") &&
                    (isPicked || picks.length < 10)
                  ) {
                    e.preventDefault();
                    onTogglePick(movie.movie_id);
                  }
                }}
              >
                <Flex justify="space-between" align="start">
                  <Box flex="1" mr={2}>
                    <Text fontSize="sm" fontWeight="600" color="brand.espresso">
                      {movie.title}
                    </Text>
                    <Text fontSize="xs" color="brand.espressoLight" mt={0.5}>
                      {movie.genres}
                    </Text>
                  </Box>
                  {isPicked && (
                    <Badge
                      bg="brand.teal"
                      color="white"
                      borderRadius="full"
                      fontSize="xs"
                      px={2}
                    >
                      ✓
                    </Badge>
                  )}
                </Flex>
              </Box>
            );
          })}
        </Grid>
      </Box>
    </VStack>
  );
}
