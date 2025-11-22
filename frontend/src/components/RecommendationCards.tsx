import { Box, SimpleGrid, Tabs, Text } from "@chakra-ui/react";
import { AnimatePresence, motion } from "framer-motion";

import type { AlgorithmName, SimulationStep } from "../types/simulation";

/** Algorithm display config — label, color, and tab value. */
const ALGORITHMS: {
  key: AlgorithmName;
  label: string;
  color: string;
}[] = [
  { key: "popularity", label: "Popularity", color: "#C8553D" },
  { key: "content_based", label: "Content-Based", color: "#588B8B" },
  { key: "collaborative", label: "Collaborative", color: "#F2C078" },
  { key: "hybrid", label: "Hybrid", color: "#8B5CF6" },
];

interface RecommendationCardsProps {
  steps: SimulationStep[];
}

/**
 * Tabbed display of top-10 recommended movies per algorithm.
 *
 * Shows the recommendations from the latest simulation step,
 * grouped by algorithm in a tabbed view. Each movie card shows
 * the title, genres, and predicted score. Cards animate in
 * when switching tabs or when new steps arrive.
 */
export default function RecommendationCards({
  steps,
}: RecommendationCardsProps) {
  const currentStep = steps.length > 0 ? steps[steps.length - 1] : null;

  if (!currentStep) {
    return null;
  }

  // Build a map of algorithm → recommendations for the current step
  const resultsByAlgo = new Map(
    currentStep.results.map((r) => [r.algorithm, r]),
  );

  return (
    <Box bg="white" p={4} borderRadius="lg" shadow="sm" mt={4}>
      <Text fontSize="sm" fontWeight="600" color="brand.espresso" mb={3}>
        Top-10 Recommendations — Step {currentStep.step_number}
      </Text>

      <Tabs.Root defaultValue="popularity" variant="line" size="sm">
        <Tabs.List>
          {ALGORITHMS.map((algo) => (
            <Tabs.Trigger
              key={algo.key}
              value={algo.key}
              style={{ fontSize: "13px" }}
              _selected={{ color: algo.color, borderColor: algo.color }}
            >
              {algo.label}
            </Tabs.Trigger>
          ))}
        </Tabs.List>

        {ALGORITHMS.map((algo) => {
          const result = resultsByAlgo.get(algo.key);
          const recommendations = result?.recommendations ?? [];

          return (
            <Tabs.Content key={algo.key} value={algo.key} pt={3}>
              <AnimatePresence mode="wait">
                <motion.div
                  key={`${algo.key}-${currentStep.step_number}`}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.3 }}
                >
                  {recommendations.length === 0 ? (
                    <Text
                      fontSize="sm"
                      color="brand.espressoLight"
                      fontStyle="italic"
                    >
                      No recommendations available yet.
                    </Text>
                  ) : (
                    <SimpleGrid columns={{ base: 1, md: 2 }} gap={2}>
                      {recommendations.slice(0, 10).map((movie, index) => (
                        <Box
                          key={movie.movie_id}
                          p={2.5}
                          borderRadius="md"
                          borderWidth="1px"
                          borderColor="brand.linenDark"
                          bg="brand.linen"
                          _hover={{ shadow: "sm" }}
                          transition="all 0.2s"
                        >
                          <Text fontSize="xs" fontWeight="600" lineClamp={1}>
                            <Text as="span" color={algo.color} mr={1}>
                              {index + 1}.
                            </Text>
                            {movie.title}
                          </Text>
                          <Text
                            fontSize="xs"
                            color="brand.espressoLight"
                            mt={0.5}
                          >
                            {movie.genres}
                          </Text>
                          {movie.score != null && (
                            <Text
                              fontSize="xs"
                              fontWeight="500"
                              color={algo.color}
                              mt={0.5}
                            >
                              Score: {movie.score.toFixed(2)}
                            </Text>
                          )}
                        </Box>
                      ))}
                    </SimpleGrid>
                  )}
                </motion.div>
              </AnimatePresence>
            </Tabs.Content>
          );
        })}
      </Tabs.Root>
    </Box>
  );
}
