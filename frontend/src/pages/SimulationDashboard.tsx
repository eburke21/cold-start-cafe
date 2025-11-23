import { useEffect, useRef, useState } from "react";
import {
  Box,
  Button,
  Grid,
  Heading,
  HStack,
  Skeleton,
  Text,
  VStack,
} from "@chakra-ui/react";

import AlgorithmTimeline from "../components/AlgorithmTimeline";
import MetricsChart from "../components/MetricsChart";
import NarratorPanel from "../components/NarratorPanel";
import RecommendationCards from "../components/RecommendationCards";
import SignalFilmstrip from "../components/SignalFilmstrip";
import MovieSearchModal from "../components/MovieSearchModal";
import type { MovieSearchModalMode } from "../components/MovieSearchModal";
import SignalPanel from "../components/SignalPanel";
import { toaster } from "../utils/toaster";
import { useSimulation } from "../hooks/useSimulation";

/** Loading skeleton matching the timeline + chart shape */
function LoadingSkeleton() {
  return (
    <VStack gap={4} align="stretch">
      {/* Timeline skeleton */}
      <Box bg="white" p={4} borderRadius="lg" shadow="sm">
        <Skeleton height="12px" width="100px" mb={3} />
        {[1, 2, 3, 4].map((i) => (
          <HStack key={i} gap={2} mb={2}>
            <Skeleton height="12px" width="80px" />
            <Skeleton height="22px" flex={1} />
          </HStack>
        ))}
      </Box>
      {/* Chart skeleton */}
      <Box bg="white" p={4} borderRadius="lg" shadow="sm">
        <HStack gap={2} mb={3}>
          <Skeleton height="28px" width="90px" borderRadius="full" />
          <Skeleton height="28px" width="80px" borderRadius="full" />
          <Skeleton height="28px" width="80px" borderRadius="full" />
        </HStack>
        <Skeleton height="320px" borderRadius="md" />
      </Box>
    </VStack>
  );
}

/** Friendly empty state for step 0 — no signals added yet */
function EmptyState() {
  return (
    <Box textAlign="center" py={12}>
      <Text fontSize="4xl" mb={3}>
        🍳
      </Text>
      <Heading
        as="h4"
        size="md"
        color="brand.espresso"
        fontFamily="heading"
        mb={2}
      >
        The kitchen is empty
      </Heading>
      <Text color="brand.espressoLight" fontSize="sm" maxW="300px" mx="auto">
        Add your first signal to get cooking! Use the panel on the left to rate a
        movie, set demographics, choose genres, or add viewing history.
      </Text>
      <Text fontSize="2xl" mt={4}>
        👈
      </Text>
    </Box>
  );
}

export default function SimulationDashboard() {
  const {
    sessionId,
    steps,
    ratingsCount,
    hasDemographics,
    genrePreferences,
    viewHistoryCount,
    isLoading,
    error,
    createSimulation,
    addRating,
    setDemographics,
    setGenrePreferences,
    addViewHistory,
    reset,
  } = useSimulation();
  const hasInitialized = useRef(false);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<MovieSearchModalMode>("rating");

  // Auto-create simulation on mount
  useEffect(() => {
    if (!sessionId && !hasInitialized.current) {
      hasInitialized.current = true;
      createSimulation();
    }
  }, [sessionId, createSimulation]);

  // Show error toasts
  useEffect(() => {
    if (error) {
      toaster.create({
        title: "Error",
        description: error,
        type: "error",
      });
    }
  }, [error]);

  const openRatingModal = () => {
    setModalMode("rating");
    setModalOpen(true);
  };

  const openViewHistoryModal = () => {
    setModalMode("viewHistory");
    setModalOpen(true);
  };

  return (
    <Box>
      {/* Top bar */}
      <HStack
        px={6}
        py={3}
        bg="white"
        borderBottomWidth="1px"
        borderColor="brand.linenDark"
        justify="space-between"
      >
        <Heading as="h2" size="md" color="brand.espresso" fontFamily="heading">
          Simulation
        </Heading>
        <Button
          size="sm"
          bg="brand.terracotta"
          color="white"
          _hover={{ bg: "brand.terracottaDark" }}
          onClick={() => {
            hasInitialized.current = true;
            reset();
            createSimulation();
          }}
          disabled={isLoading}
        >
          New Simulation
        </Button>
      </HStack>

      {/* Session expired / fatal error state */}
      {error && !sessionId && (
        <Box textAlign="center" py={20} px={8}>
          <Text fontSize="4xl" mb={3}>
            ☕
          </Text>
          <Heading
            as="h3"
            size="lg"
            color="brand.espresso"
            fontFamily="heading"
            mb={2}
          >
            Your table&apos;s been cleared!
          </Heading>
          <Text color="brand.espressoLight" mb={6} maxW="400px" mx="auto">
            {error}
          </Text>
          <Button
            bg="brand.terracotta"
            color="white"
            _hover={{ bg: "brand.terracottaDark" }}
            onClick={() => {
              hasInitialized.current = true;
              reset();
              createSimulation();
            }}
          >
            Start a New Simulation
          </Button>
        </Box>
      )}

      {/* Three-column layout (hidden when session expired) */}
      <Grid
        templateColumns={{ base: "1fr", lg: "280px 1fr 300px" }}
        gap={0}
        minH="calc(100vh - 120px)"
        display={error && !sessionId ? "none" : undefined}
      >
        {/* Left: Signal Panel */}
        <Box
          bg="white"
          borderRightWidth={{ lg: "1px" }}
          borderColor="brand.linenDark"
          p={4}
        >
          <SignalPanel
            ratingsCount={ratingsCount}
            hasDemographics={hasDemographics}
            genrePreferences={genrePreferences}
            viewHistoryCount={viewHistoryCount}
            isLoading={isLoading}
            onOpenRatingModal={openRatingModal}
            onOpenViewHistoryModal={openViewHistoryModal}
            onSetDemographics={setDemographics}
            onSetGenrePreferences={setGenrePreferences}
          />
        </Box>

        {/* Center: Metrics chart + timeline */}
        <Box p={6} overflowY="auto">
          <Heading
            as="h3"
            size="sm"
            color="brand.espresso"
            mb={4}
            fontFamily="heading"
          >
            Algorithm Performance
          </Heading>
          {isLoading && steps.length === 0 ? (
            <LoadingSkeleton />
          ) : steps.length <= 1 ? (
            <>
              <AlgorithmTimeline steps={steps} />
              <EmptyState />
            </>
          ) : (
            <>
              <AlgorithmTimeline steps={steps} />
              <SignalFilmstrip steps={steps} />
              <MetricsChart steps={steps} />
              <RecommendationCards steps={steps} />
            </>
          )}
        </Box>

        {/* Right: Narrator panel */}
        <Box
          bg="brand.linenDark"
          borderLeftWidth={{ lg: "1px" }}
          borderColor="brand.linenDark"
          p={4}
          overflowY="auto"
        >
          <Heading
            as="h3"
            size="sm"
            color="brand.espresso"
            mb={4}
            fontFamily="heading"
          >
            ☕ Narrator
          </Heading>
          <NarratorPanel steps={steps} sessionId={sessionId} />
        </Box>
      </Grid>

      {/* Movie search/rate modal */}
      <MovieSearchModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        mode={modalMode}
        onRate={addRating}
        onAddViewHistory={addViewHistory}
      />
    </Box>
  );
}
