import { useCallback, useEffect, useState } from "react";
import {
  Box,
  Button,
  Checkbox,
  Dialog,
  Flex,
  HStack,
  Input,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react";

import * as api from "../api/client";
import type { MovieSearchResult } from "../types/movies";

/** 5-star rating widget using clickable star buttons. */
function StarRating({
  value,
  onChange,
}: {
  value: number;
  onChange: (score: number) => void;
}) {
  return (
    <HStack gap={1}>
      {[1, 2, 3, 4, 5].map((star) => (
        <Button
          key={star}
          size="xs"
          variant="ghost"
          onClick={() => onChange(star)}
          color={star <= value ? "brand.honey" : "gray.300"}
          fontSize="lg"
          px={1}
          minW="auto"
          transition="transform 0.15s ease"
          _hover={{ transform: "scale(1.3)" }}
        >
          ★
        </Button>
      ))}
    </HStack>
  );
}

export type MovieSearchModalMode = "rating" | "viewHistory";

interface MovieSearchModalProps {
  open: boolean;
  onClose: () => void;
  mode: MovieSearchModalMode;
  onRate: (movieId: number, score: number) => Promise<void>;
  onAddViewHistory: (movieIds: number[]) => Promise<void>;
}

export default function MovieSearchModal({
  open,
  onClose,
  mode,
  onRate,
  onAddViewHistory,
}: MovieSearchModalProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<MovieSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // Rating mode state
  const [selectedMovieId, setSelectedMovieId] = useState<number | null>(null);
  const [rating, setRating] = useState(0);

  // View history mode state
  const [checkedMovies, setCheckedMovies] = useState<Set<number>>(new Set());

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const movies = await api.searchMovies(query, 20);
        setResults(movies);
      } catch {
        setResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!open) {
      setQuery("");
      setResults([]);
      setSelectedMovieId(null);
      setRating(0);
      setCheckedMovies(new Set());
    }
  }, [open]);

  const handleRate = useCallback(async () => {
    if (selectedMovieId === null || rating === 0) return;
    await onRate(selectedMovieId, rating);
    onClose();
  }, [selectedMovieId, rating, onRate, onClose]);

  const handleAddHistory = useCallback(async () => {
    if (checkedMovies.size === 0) return;
    await onAddViewHistory(Array.from(checkedMovies));
    onClose();
  }, [checkedMovies, onAddViewHistory, onClose]);

  const toggleCheck = (movieId: number) => {
    setCheckedMovies((prev) => {
      const next = new Set(prev);
      if (next.has(movieId)) {
        next.delete(movieId);
      } else {
        next.add(movieId);
      }
      return next;
    });
  };

  return (
    <Dialog.Root open={open} onOpenChange={(e) => !e.open && onClose()}>
      <Dialog.Backdrop />
      <Dialog.Positioner>
        <Dialog.Content maxW="lg" maxH="80vh">
          <Dialog.Header>
            <Dialog.Title>
              {mode === "rating" ? "Rate a Movie" : "Add to View History"}
            </Dialog.Title>
            <Dialog.CloseTrigger />
          </Dialog.Header>

          <Dialog.Body>
            <VStack gap={4} align="stretch">
              {/* Search input */}
              <Input
                placeholder="Search movies by title..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                autoFocus
              />

              {/* Loading */}
              {isSearching && (
                <Flex justify="center" py={4}>
                  <Spinner size="sm" color="brand.teal" />
                </Flex>
              )}

              {/* Results */}
              <Box maxH="400px" overflowY="auto">
                {results.length === 0 && query.trim() && !isSearching && (
                  <Text color="brand.espressoLight" textAlign="center" py={4}>
                    No movies found.
                  </Text>
                )}

                <VStack gap={1} align="stretch">
                  {results.map((movie) => (
                    <Box
                      key={movie.movie_id}
                      p={3}
                      borderRadius="md"
                      bg={
                        selectedMovieId === movie.movie_id
                          ? "brand.linenDark"
                          : "transparent"
                      }
                      _hover={{ bg: "brand.linenDark" }}
                      cursor="pointer"
                      onClick={() => {
                        if (mode === "rating") {
                          setSelectedMovieId(movie.movie_id);
                        }
                      }}
                    >
                      <Flex justify="space-between" align="center">
                        <Box flex="1">
                          <HStack gap={2}>
                            {mode === "viewHistory" && (
                              <Checkbox.Root
                                checked={checkedMovies.has(movie.movie_id)}
                                onCheckedChange={() =>
                                  toggleCheck(movie.movie_id)
                                }
                              >
                                <Checkbox.HiddenInput />
                                <Checkbox.Control />
                              </Checkbox.Root>
                            )}
                            <Box>
                              <Text fontSize="sm" fontWeight="500">
                                {movie.title}
                              </Text>
                              <Text fontSize="xs" color="brand.espressoLight">
                                {movie.genres}
                              </Text>
                            </Box>
                          </HStack>
                        </Box>

                        {/* Star rating for selected movie in rating mode */}
                        {mode === "rating" &&
                          selectedMovieId === movie.movie_id && (
                            <StarRating value={rating} onChange={setRating} />
                          )}
                      </Flex>
                    </Box>
                  ))}
                </VStack>
              </Box>
            </VStack>
          </Dialog.Body>

          <Dialog.Footer>
            <HStack gap={3}>
              <Button variant="outline" onClick={onClose} size="sm">
                Cancel
              </Button>
              {mode === "rating" ? (
                <Button
                  bg="brand.terracotta"
                  color="white"
                  _hover={{ bg: "brand.terracottaDark" }}
                  onClick={handleRate}
                  disabled={selectedMovieId === null || rating === 0}
                  size="sm"
                >
                  Rate ({rating}/5)
                </Button>
              ) : (
                <Button
                  bg="brand.teal"
                  color="white"
                  _hover={{ bg: "brand.tealDark" }}
                  onClick={handleAddHistory}
                  disabled={checkedMovies.size === 0}
                  size="sm"
                >
                  Add {checkedMovies.size} Movie
                  {checkedMovies.size !== 1 ? "s" : ""}
                </Button>
              )}
            </HStack>
          </Dialog.Footer>
        </Dialog.Content>
      </Dialog.Positioner>
    </Dialog.Root>
  );
}
