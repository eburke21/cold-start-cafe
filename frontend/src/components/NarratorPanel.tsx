import { useEffect, useRef } from "react";
import { Box, Text, VStack } from "@chakra-ui/react";

import { useTypingAnimation } from "../hooks/useTypingAnimation";
import type { SimulationStep } from "../types/simulation";

/**
 * A single narration card with optional typing animation.
 * Only the most recent narration gets the typing effect —
 * previous narrations display their full text instantly.
 */
function NarrationCard({
  step,
  isLatest,
}: {
  step: SimulationStep;
  isLatest: boolean;
}) {
  const displayedText = useTypingAnimation(step.narration, 30, !isLatest);

  return (
    <Box
      bg="white"
      p={3}
      borderRadius="lg"
      shadow="sm"
      borderLeftWidth="3px"
      borderLeftColor={isLatest ? "brand.terracotta" : "brand.honey"}
      position="relative"
      /* Speech bubble tail effect via ::before pseudo-element */
      _before={{
        content: '""',
        position: "absolute",
        left: "-8px",
        top: "12px",
        width: 0,
        height: 0,
        borderTop: "6px solid transparent",
        borderBottom: "6px solid transparent",
        borderRight: "8px solid white",
      }}
    >
      <Text fontSize="xs" fontWeight="600" color="brand.espressoLight" mb={1}>
        Step {step.step_number}
        {step.signal_added ? ` — ${step.signal_added.type}` : ""}
      </Text>
      <Text fontSize="sm" lineHeight="1.6" color="brand.espresso">
        {displayedText}
        {isLatest && displayedText.length < step.narration.length && (
          <Text as="span" animation="blink 1s steps(1) infinite">
            ▌
          </Text>
        )}
      </Text>
    </Box>
  );
}

interface NarratorPanelProps {
  steps: SimulationStep[];
}

/**
 * Right sidebar panel showing narration for each simulation step.
 *
 * Features:
 * - Café-themed speech-bubble cards with warm tones
 * - Typing animation on the most recent narration
 * - Auto-scrolls to the latest narration
 */
export default function NarratorPanel({ steps }: NarratorPanelProps) {
  const endRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the latest narration when steps change
  useEffect(() => {
    if (endRef.current) {
      endRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [steps.length]);

  if (steps.length === 0) {
    return (
      <Box textAlign="center" py={8}>
        <Text fontSize="2xl" mb={2}>
          ☕
        </Text>
        <Text color="brand.espressoLight" fontStyle="italic" fontSize="sm">
          The barista is waiting for your first order...
        </Text>
      </Box>
    );
  }

  return (
    <VStack gap={3} align="stretch" pl={2}>
      {steps.map((step, index) => (
        <NarrationCard
          key={step.step_number}
          step={step}
          isLatest={index === steps.length - 1}
        />
      ))}
      <div ref={endRef} />
    </VStack>
  );
}
