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

import MovieSearchModal from "../components/MovieSearchModal";
import type { MovieSearchModalMode } from "../components/MovieSearchModal";
import SignalPanel from "../components/SignalPanel";
import { toaster } from "../utils/toaster";
import { useSimulation } from "../hooks/useSimulation";
import type { SimulationStep } from "../types/simulation";

/**
 * Temporary debug view showing raw step data as formatted cards.
 * Will be replaced by MetricsChart + AlgorithmTimeline in Phase 5.
 */
function DebugStepView({ steps }: { steps: SimulationStep[] }) {
  if (steps.length === 0) {
    return (
      <Text color="brand.espressoLight" fontStyle="italic">
        No simulation data yet.
      </Text>
    );
  }

  return (
    <VStack gap={4} align="stretch">
      {steps.map((step) => (
        <Box
          key={step.step_number}
          bg="white"
          p={4}
          borderRadius="md"
          shadow="sm"
        >
          <Text fontWeight="600" mb={2}>
            Step {step.step_number}
            {step.signal_added
              ? ` — ${step.signal_added.type}`
              : " — Initial (no signals)"}
          </Text>
          {step.results.map((result) => (
            <HStack key={result.algorithm} justify="space-between" py={1}>
              <Text fontSize="sm" fontWeight="500">
                {result.algorithm}
              </Text>
              <Text fontSize="xs" color="brand.espressoLight">
                P@10: {result.precision_at_10.toFixed(3)} | R@10:{" "}
                {result.recall_at_10.toFixed(3)} | NDCG:{" "}
                {result.ndcg_at_10.toFixed(3)}
              </Text>
            </HStack>
          ))}
        </Box>
      ))}
    </VStack>
  );
}

/**
 * Temporary narration view showing narration text for each step.
 * Will be replaced by NarratorPanel in Phase 5.
 */
function NarrationView({ steps }: { steps: SimulationStep[] }) {
  if (steps.length === 0) {
    return (
      <Text color="brand.espressoLight" fontStyle="italic" fontSize="sm">
        Start a simulation to see narration.
      </Text>
    );
  }

  return (
    <VStack gap={3} align="stretch">
      {steps.map((step) => (
        <Box
          key={step.step_number}
          bg="white"
          p={3}
          borderRadius="md"
          shadow="sm"
          borderLeftWidth="3px"
          borderLeftColor="brand.honey"
        >
          <Text fontSize="xs" fontWeight="600" color="brand.espressoLight">
            Step {step.step_number}
          </Text>
          <Text fontSize="sm" mt={1}>
            {step.narration}
          </Text>
        </Box>
      ))}
    </VStack>
  );
}

/** Loading skeleton for the center panel */
function LoadingSkeleton() {
  return (
    <VStack gap={4} align="stretch">
      {[1, 2, 3].map((i) => (
        <Box key={i} bg="white" p={4} borderRadius="md" shadow="sm">
          <Skeleton height="16px" width="200px" mb={3} />
          <Skeleton height="12px" width="100%" mb={2} />
          <Skeleton height="12px" width="100%" mb={2} />
          <Skeleton height="12px" width="80%" />
        </Box>
      ))}
    </VStack>
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

      {/* Three-column layout */}
      <Grid
        templateColumns={{ base: "1fr", lg: "280px 1fr 300px" }}
        gap={0}
        minH="calc(100vh - 120px)"
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

        {/* Center: Debug data view (replaced by charts in Phase 5) */}
        <Box p={6} overflowY="auto">
          <Heading
            as="h3"
            size="sm"
            color="brand.espresso"
            mb={4}
            fontFamily="heading"
          >
            Algorithm Results
          </Heading>
          {isLoading && steps.length === 0 ? (
            <LoadingSkeleton />
          ) : (
            <DebugStepView steps={steps} />
          )}
        </Box>

        {/* Right: Narration panel */}
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
            Narrator
          </Heading>
          <NarrationView steps={steps} />
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
