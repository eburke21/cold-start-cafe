import { useEffect, useRef } from "react";
import { Box, HStack, Text } from "@chakra-ui/react";
import { motion } from "framer-motion";

import type { SimulationStep } from "../types/simulation";

/**
 * Build a human-readable label + icon for a signal chip.
 * Extracts key info from the signal payload for compact display.
 */
function chipContent(step: SimulationStep): { icon: string; label: string } {
  if (!step.signal_added) {
    return { icon: "🍽", label: "Start" };
  }

  const payload = step.signal_added.payload;
  switch (step.signal_added.type) {
    case "rating": {
      const score = (payload as Record<string, unknown>).score;
      return { icon: "⭐", label: `Rated ${score ?? "?"}` };
    }
    case "demographic": {
      const age = (payload as Record<string, unknown>).age;
      const gender = (payload as Record<string, unknown>).gender;
      const parts = [age, gender].filter(Boolean);
      return {
        icon: "👤",
        label: parts.length > 0 ? parts.join("/") : "Demo",
      };
    }
    case "genre_preference": {
      const genres = (payload as Record<string, unknown>).genres;
      const count = Array.isArray(genres) ? genres.length : 0;
      return { icon: "🎬", label: `${count} genre${count !== 1 ? "s" : ""}` };
    }
    case "view_history": {
      const movieIds = (payload as Record<string, unknown>).movie_ids;
      const count = Array.isArray(movieIds) ? movieIds.length : 0;
      return {
        icon: "👁",
        label: `${count} view${count !== 1 ? "s" : ""}`,
      };
    }
    default:
      return { icon: "📌", label: step.signal_added.type };
  }
}

interface SignalFilmstripProps {
  steps: SimulationStep[];
}

/**
 * Horizontal scrollable strip showing each signal as a compact chip.
 * Auto-scrolls to the latest signal when new steps arrive.
 */
export default function SignalFilmstrip({ steps }: SignalFilmstripProps) {
  const endRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest chip when steps change
  useEffect(() => {
    if (endRef.current) {
      endRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [steps.length]);

  if (steps.length === 0) {
    return null;
  }

  return (
    <Box
      overflowX="auto"
      py={2}
      px={1}
      css={{
        "&::-webkit-scrollbar": { height: "4px" },
        "&::-webkit-scrollbar-track": { background: "transparent" },
        "&::-webkit-scrollbar-thumb": {
          background: "#D4745F",
          borderRadius: "2px",
        },
      }}
    >
      <HStack gap={2} minW="max-content">
        {steps.map((step, index) => {
          const { icon, label } = chipContent(step);
          const isLatest = index === steps.length - 1;

          return (
            <motion.div
              key={step.step_number}
              initial={{ opacity: 0, x: 30, scale: 0.8 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 20,
                mass: 0.8,
              }}
            >
              <Box
                ref={isLatest ? endRef : undefined}
                bg={isLatest ? "brand.terracotta" : "white"}
                color={isLatest ? "white" : "brand.espresso"}
                px={3}
                py={1.5}
                borderRadius="full"
                shadow="sm"
                borderWidth="1px"
                borderColor={isLatest ? "brand.terracotta" : "brand.linenDark"}
                whiteSpace="nowrap"
                flexShrink={0}
                transition="all 0.3s"
              >
                <Text fontSize="xs" fontWeight="500">
                  <Text as="span" mr={1}>
                    {icon}
                  </Text>
                  <Text as="span" fontWeight="600" mr={1}>
                    {step.step_number}.
                  </Text>
                  {label}
                </Text>
              </Box>
            </motion.div>
          );
        })}
      </HStack>
    </Box>
  );
}
