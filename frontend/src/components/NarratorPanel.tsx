import { useEffect, useRef } from "react";
import { Box, Text, VStack } from "@chakra-ui/react";

import { useNarrationStream } from "../hooks/useNarrationStream";
import { useTypingAnimation } from "../hooks/useTypingAnimation";
import type { SimulationStep } from "../types/simulation";

/**
 * A single narration card with dual animation support.
 *
 * Template narrations get the local typing effect (useTypingAnimation).
 * LLM narrations stream via SSE — the network provides the typing feel.
 * Both hooks are always called (React rules), but only the active one
 * does real work via skip/enabled flags.
 */
function NarrationCard({
  step,
  isLatest,
  sessionId,
}: {
  step: SimulationStep;
  isLatest: boolean;
  sessionId: string | null;
}) {
  const isLlm = step.narration_source === "llm";

  // Hook 1: Local typing animation (active for template narrations on latest step)
  const typingText = useTypingAnimation(step.narration, 30, !isLatest || isLlm);

  // Hook 2: SSE stream (active for LLM narrations on latest step)
  const { text: streamedText, isStreaming } = useNarrationStream(
    sessionId,
    step.step_number,
    step.narration_source ?? "template",
    step.narration,
    isLatest && isLlm,
  );

  // Choose which text and cursor state to display
  let displayedText: string;
  let showCursor: boolean;

  if (isLlm) {
    displayedText = streamedText;
    showCursor = isStreaming;
  } else {
    displayedText = typingText;
    showCursor = isLatest && typingText.length < step.narration.length;
  }

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
        {isLlm && (
          <Text as="span" color="brand.sage" ml={1}>
            ✨
          </Text>
        )}
      </Text>
      <Text fontSize="sm" lineHeight="1.6" color="brand.espresso">
        {displayedText}
        {showCursor && (
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
  sessionId: string | null;
}

/**
 * Right sidebar panel showing narration for each simulation step.
 *
 * Features:
 * - Café-themed speech-bubble cards with warm tones
 * - Typing animation on template narrations (latest step)
 * - SSE streaming on LLM narrations (latest step, sparkle indicator)
 * - Auto-scrolls to the latest narration
 */
export default function NarratorPanel({ steps, sessionId }: NarratorPanelProps) {
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
          sessionId={sessionId}
        />
      ))}
      <div ref={endRef} />
    </VStack>
  );
}
