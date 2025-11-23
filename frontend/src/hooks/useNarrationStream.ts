/**
 * Hook that connects to the narration SSE endpoint for LLM-streamed narrations.
 *
 * When enabled, opens an EventSource to the backend's /narration/stream endpoint
 * and accumulates text chunks as they arrive. For template narrations (or when
 * not enabled), simply returns the fallback text without connecting.
 *
 * The streamed text persists in state after completion — even if `enabled`
 * becomes false (e.g., when a newer step becomes the latest), the hook
 * continues to return the completed text rather than the placeholder.
 *
 * Note: No synchronous setState in the effect body (react-hooks/set-state-in-effect).
 * Streaming state is derived from a ref + done flag; only async EventSource
 * callbacks call setState.
 */

import { useEffect, useRef, useState } from "react";

interface NarrationStreamResult {
  /** The current narration text (streamed or fallback) */
  text: string;
  /** True while SSE chunks are still arriving */
  isStreaming: boolean;
}

export function useNarrationStream(
  sessionId: string | null,
  stepNumber: number,
  narrationSource: string,
  fallbackText: string,
  enabled: boolean,
): NarrationStreamResult {
  // Text accumulated from SSE chunks (null = not started yet)
  const [streamedText, setStreamedText] = useState<string | null>(null);
  // Set to true only when the "done" event fires (in a callback, not effect body)
  const [isDone, setIsDone] = useState(false);
  // Prevents re-opening the EventSource on re-renders
  const hasStartedRef = useRef(false);

  useEffect(() => {
    if (!enabled || narrationSource !== "llm" || !sessionId || hasStartedRef.current) {
      return;
    }

    hasStartedRef.current = true;
    // No setState here — only in async event callbacks below

    const url = `/api/v1/simulation/${sessionId}/narration/stream?step=${stepNumber}`;
    const eventSource = new EventSource(url);

    eventSource.addEventListener("chunk", (event: MessageEvent) => {
      setStreamedText((prev) => (prev ?? "") + event.data);
    });

    eventSource.addEventListener("done", () => {
      setIsDone(true);
      eventSource.close();
    });

    eventSource.onerror = () => {
      setIsDone(true);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [sessionId, stepNumber, narrationSource, enabled]);

  // Derive streaming status: started but not done, with text arriving
  const isStreaming = streamedText !== null && !isDone;

  // If we've received any streamed text, use it (persists after completion)
  if (streamedText !== null) {
    return { text: streamedText, isStreaming };
  }

  return { text: fallbackText, isStreaming: false };
}
