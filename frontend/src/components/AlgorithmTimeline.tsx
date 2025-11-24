import { Box, HStack, Text, VStack } from "@chakra-ui/react";
import { motion } from "framer-motion";

import type { AlgorithmName, SimulationStep } from "../types/simulation";

/**
 * Algorithm display config — maps algorithm names to labels and raw hex colors.
 * Raw hex is needed for the Framer Motion `background` style (outside Chakra tokens).
 */
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

/** Signal type → display label for the step indicator. */
function signalLabel(step: SimulationStep): string {
  if (!step.signal_added) return "Initial";
  switch (step.signal_added.type) {
    case "rating":
      return "⭐ Rating";
    case "demographic":
      return "👤 Demographics";
    case "genre_preference":
      return "🎬 Genre Prefs";
    case "view_history":
      return "👁 View History";
    default:
      return step.signal_added.type;
  }
}

interface AlgorithmTimelineProps {
  steps: SimulationStep[];
  /** Which metric to display in the race bars. */
  metric?: "precision_at_10" | "recall_at_10" | "ndcg_at_10";
}

/**
 * Horizontal "race" visualization showing each algorithm's current metric
 * as an animated bar. The bars grow/shrink smoothly when new steps arrive.
 */
export default function AlgorithmTimeline({
  steps,
  metric = "precision_at_10",
}: AlgorithmTimelineProps) {
  const currentStep = steps.length > 0 ? steps[steps.length - 1] : null;
  const prevStep = steps.length > 1 ? steps[steps.length - 2] : null;

  if (!currentStep) {
    return null;
  }

  // Build maps of algorithm → metric value for current and previous steps
  const metricValues: Record<string, number> = {};
  for (const result of currentStep.results) {
    metricValues[result.algorithm] = result[metric];
  }

  const prevMetricValues: Record<string, number> = {};
  if (prevStep) {
    for (const result of prevStep.results) {
      prevMetricValues[result.algorithm] = result[metric];
    }
  }

  return (
    <Box
      bg="white"
      p={4}
      borderRadius="lg"
      className="cafe-card"
      mb={4}
      role="img"
      aria-label={`Algorithm performance at step ${currentStep.step_number}. ${ALGORITHMS.map(
        (a) => `${a.label}: ${((metricValues[a.key] ?? 0) * 100).toFixed(0)}%`
      ).join(", ")}`}
    >
      {/* Step indicator */}
      <HStack justify="space-between" mb={3}>
        <Text fontSize="xs" fontWeight="600" color="brand.espressoLight">
          Step {currentStep.step_number}
        </Text>
        <Text fontSize="xs" color="brand.espressoLight">
          {signalLabel(currentStep)}
        </Text>
      </HStack>

      {/* Race bars */}
      <VStack gap={2} align="stretch">
        {ALGORITHMS.map((algo) => {
          const value = metricValues[algo.key] ?? 0;
          const prevValue = prevMetricValues[algo.key] ?? 0;
          const percentage = Math.max(value * 100, 2); // min 2% for visibility
          const improved = value - prevValue > 0.05;
          const bigJump = value - prevValue > 0.1;

          return (
            <HStack key={algo.key} gap={2}>
              <HStack
                gap={1}
                w="90px"
                flexShrink={0}
              >
                <Box
                  w="8px"
                  h="8px"
                  borderRadius="full"
                  bg={algo.color}
                  flexShrink={0}
                />
                <Text
                  fontSize="xs"
                  fontWeight="500"
                  color="brand.espresso"
                >
                  {algo.label}
                </Text>
              </HStack>

              {/* Bar track */}
              <Box
                flex={1}
                h="22px"
                bg="brand.linenDark"
                borderRadius="md"
                overflow="hidden"
                position="relative"
              >
                {/* Animated bar with optional improvement flash */}
                <motion.div
                  style={{
                    height: "100%",
                    background: algo.color,
                    borderRadius: "6px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "flex-end",
                    paddingRight: "6px",
                  }}
                  animate={{
                    width: `${percentage}%`,
                    opacity: improved ? [1, 0.5, 1, 0.7, 1] : 1,
                  }}
                  transition={{
                    width: { duration: 0.8, ease: "easeOut" },
                    opacity: { duration: 0.6, ease: "easeInOut" },
                  }}
                >
                  <Text
                    as="span"
                    fontSize="10px"
                    fontWeight="700"
                    color="white"
                    lineHeight="1"
                    fontFamily="mono"
                  >
                    {value.toFixed(2)}
                  </Text>
                </motion.div>

                {/* Sparkle burst for big jumps (>0.1 increase) */}
                {bigJump && (
                  <motion.div
                    key={`spark-${algo.key}-${currentStep.step_number}`}
                    initial={{ scale: 0, opacity: 1 }}
                    animate={{ scale: [0, 1.5, 0], opacity: [1, 0.8, 0] }}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                    style={{
                      position: "absolute",
                      right: "8px",
                      top: "50%",
                      transform: "translateY(-50%)",
                      fontSize: "14px",
                      pointerEvents: "none",
                    }}
                  >
                    ✨
                  </motion.div>
                )}
              </Box>
            </HStack>
          );
        })}
      </VStack>
    </Box>
  );
}
