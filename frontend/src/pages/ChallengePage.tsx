/**
 * Challenge mode page — three-phase state machine:
 *
 * 1. Setup: Target user card (demographics + 3 seed ratings), "Start Challenge"
 * 2. Picking: Movie search/browse interface to pick 10 movies
 * 3. Results: Score comparison, narration, ground-truth reveal
 *
 * Uses the useChallenge hook for state management (same pattern as
 * SimulationDashboard's useSimulation).
 */

import { useEffect, useRef } from "react";
import {
  Badge,
  Box,
  Button,
  Flex,
  Grid,
  HStack,
  Heading,
  Skeleton,
  Text,
  VStack,
} from "@chakra-ui/react";
import { motion } from "framer-motion";

import MoviePicker from "../components/MoviePicker";
import ScoreComparison from "../components/ScoreComparison";
import { useChallenge } from "../hooks/useChallenge";
import { toaster } from "../utils/toaster";

export default function ChallengePage() {
  const challenge = useChallenge();
  const hasCreatedRef = useRef(false);

  // Auto-create challenge on mount (same pattern as useSimulation)
  useEffect(() => {
    if (!hasCreatedRef.current) {
      hasCreatedRef.current = true;
      challenge.createChallenge();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Show error toasts
  useEffect(() => {
    if (challenge.error) {
      toaster.create({
        title: "Challenge Error",
        description: challenge.error,
        type: "error",
      });
    }
  }, [challenge.error]);

  // Loading state
  if (challenge.isLoading && !challenge.sessionId) {
    return (
      <Box maxW="900px" mx="auto" p={6}>
        <Skeleton height="40px" mb={4} />
        <Skeleton height="200px" mb={4} />
        <Skeleton height="100px" />
      </Box>
    );
  }

  return (
    <Box maxW="900px" mx="auto" p={6}>
      {challenge.phase === "setup" && challenge.targetUser && (
        <SetupPhase
          targetUser={challenge.targetUser}
          onStart={challenge.startPicking}
        />
      )}

      {challenge.phase === "picking" && (
        <MoviePicker
          availableMovies={challenge.availableMovies}
          picks={challenge.picks}
          onTogglePick={challenge.togglePick}
          onRemovePick={challenge.removePick}
          onSubmit={challenge.submitPicks}
          isLoading={challenge.isLoading}
        />
      )}

      {challenge.phase === "results" &&
        challenge.userScore &&
        challenge.algoScores.length > 0 && (
          <ResultsPhase
            userScore={challenge.userScore}
            algoScores={challenge.algoScores}
            narration={challenge.narration}
            groundTruthFavorites={challenge.groundTruthFavorites}
            onTryAgain={challenge.tryAgain}
            isLoading={challenge.isLoading}
          />
        )}
    </Box>
  );
}

// --- Setup Phase ---

function SetupPhase({
  targetUser,
  onStart,
}: {
  targetUser: NonNullable<ReturnType<typeof useChallenge>["targetUser"]>;
  onStart: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <VStack gap={6} align="stretch">
        {/* Header */}
        <Box textAlign="center">
          <Heading as="h2" size="xl" color="brand.espresso" mb={2}>
            Challenge Mode
          </Heading>
          <Text color="brand.espressoLight" maxW="600px" mx="auto">
            Can you recommend movies better than the algorithms? Study this
            user&apos;s profile, then pick 10 movies you think they&apos;d love.
          </Text>
        </Box>

        {/* Target user card */}
        <Box bg="white" p={6} borderRadius="xl" shadow="md">
          <Text
            fontSize="sm"
            fontWeight="700"
            color="brand.teal"
            textTransform="uppercase"
            letterSpacing="wide"
            mb={3}
          >
            Target User Profile
          </Text>

          {/* Demographics */}
          <HStack gap={3} mb={4} wrap="wrap">
            {targetUser.demographics.age && (
              <Badge bg="brand.linenDark" color="brand.espresso" px={3} py={1}>
                Age {targetUser.demographics.age}
              </Badge>
            )}
            {targetUser.demographics.gender && (
              <Badge bg="brand.linenDark" color="brand.espresso" px={3} py={1}>
                {targetUser.demographics.gender === "M" ? "Male" : "Female"}
              </Badge>
            )}
            {targetUser.demographics.occupation && (
              <Badge bg="brand.linenDark" color="brand.espresso" px={3} py={1}>
                {targetUser.demographics.occupation}
              </Badge>
            )}
          </HStack>

          {/* Seed ratings */}
          <Text
            fontSize="sm"
            fontWeight="600"
            color="brand.espresso"
            mb={2}
          >
            Movies they loved:
          </Text>
          <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={3}>
            {targetUser.seed_ratings.map((rating) => (
              <Box
                key={rating.movie_id}
                p={3}
                bg="brand.linen"
                borderRadius="lg"
                borderLeftWidth="3px"
                borderLeftColor="brand.honey"
              >
                <Text fontSize="sm" fontWeight="600" color="brand.espresso">
                  {rating.title}
                </Text>
                <Text fontSize="xs" color="brand.espressoLight">
                  {rating.genres}
                </Text>
                <HStack gap={1} mt={1}>
                  {[1, 2, 3, 4, 5].map((star) => (
                    <Text
                      key={star}
                      fontSize="xs"
                      color={
                        rating.score !== null && star <= rating.score
                          ? "brand.honey"
                          : "gray.300"
                      }
                    >
                      ★
                    </Text>
                  ))}
                </HStack>
              </Box>
            ))}
          </Grid>
        </Box>

        {/* Start button */}
        <Flex justify="center">
          <Button
            bg="brand.terracotta"
            color="white"
            size="lg"
            _hover={{ bg: "brand.terracottaDark" }}
            onClick={onStart}
          >
            Start Challenge
          </Button>
        </Flex>
      </VStack>
    </motion.div>
  );
}

// --- Results Phase ---

function ResultsPhase({
  userScore,
  algoScores,
  narration,
  groundTruthFavorites,
  onTryAgain,
  isLoading,
}: {
  userScore: NonNullable<ReturnType<typeof useChallenge>["userScore"]>;
  algoScores: ReturnType<typeof useChallenge>["algoScores"];
  narration: string;
  groundTruthFavorites: ReturnType<typeof useChallenge>["groundTruthFavorites"];
  onTryAgain: () => Promise<void>;
  isLoading: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <VStack gap={6} align="stretch">
        {/* Score comparison */}
        <ScoreComparison userScore={userScore} algoScores={algoScores} />

        {/* Narration */}
        {narration && (
          <Box
            bg="white"
            p={4}
            borderRadius="lg"
            shadow="sm"
            borderLeftWidth="3px"
            borderLeftColor="brand.terracotta"
          >
            <Text fontSize="xs" fontWeight="600" color="brand.teal" mb={1}>
              The Barista&apos;s Verdict
            </Text>
            <Text fontSize="sm" lineHeight="1.6" color="brand.espresso">
              {narration}
            </Text>
          </Box>
        )}

        {/* Ground-truth reveal */}
        <GroundTruthReveal favorites={groundTruthFavorites} />

        {/* Try Again */}
        <Flex justify="center">
          <Button
            bg="brand.teal"
            color="white"
            size="lg"
            _hover={{ bg: "brand.tealDark" }}
            onClick={onTryAgain}
            disabled={isLoading}
          >
            Try Again with a Different User
          </Button>
        </Flex>
      </VStack>
    </motion.div>
  );
}

// --- Ground-truth reveal ---

function GroundTruthReveal({
  favorites,
}: {
  favorites: ReturnType<typeof useChallenge>["groundTruthFavorites"];
}) {
  if (favorites.length === 0) return null;

  return (
    <Box bg="white" p={4} borderRadius="lg" shadow="sm">
      <Text fontSize="sm" fontWeight="600" color="brand.espresso" mb={3}>
        What They Actually Loved
      </Text>
      <Text fontSize="xs" color="brand.espressoLight" mb={3}>
        These are the target user&apos;s actual top-rated movies — see how your
        picks compare!
      </Text>
      <Grid templateColumns="repeat(auto-fit, minmax(180px, 1fr))" gap={2}>
        {favorites.map((movie, idx) => (
          <HStack
            key={movie.movie_id}
            p={2}
            bg="brand.linen"
            borderRadius="md"
            gap={2}
          >
            <Text
              fontSize="xs"
              fontWeight="bold"
              color="brand.teal"
              minW="18px"
            >
              #{idx + 1}
            </Text>
            <Box flex="1">
              <Text fontSize="xs" fontWeight="500" color="brand.espresso">
                {movie.title}
              </Text>
              <Text fontSize="2xs" color="brand.espressoLight">
                {movie.genres} · {movie.score}/5
              </Text>
            </Box>
          </HStack>
        ))}
      </Grid>
    </Box>
  );
}
