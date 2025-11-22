import { useEffect, useState } from "react";

/**
 * Hook that reveals text progressively, one character at a time.
 *
 * Returns the portion of `text` that should be visible so far.
 * If `skip` is true, the full text is returned immediately (no animation).
 *
 * Reset behavior: When the consuming component remounts (via React `key`),
 * the hook state naturally resets. This avoids the need for a setState-in-effect
 * reset pattern.
 *
 * @param text   Full text to reveal
 * @param speed  Milliseconds per character (default 30ms)
 * @param skip   If true, skip animation and show full text
 */
export function useTypingAnimation(
  text: string,
  speed: number = 30,
  skip: boolean = false,
): string {
  const [charIndex, setCharIndex] = useState(0);

  useEffect(() => {
    if (skip || charIndex >= text.length) return;

    const timer = setTimeout(() => {
      setCharIndex((i) => i + 1);
    }, speed);

    return () => clearTimeout(timer);
  }, [charIndex, text.length, speed, skip]);

  if (skip) return text;
  return text.slice(0, charIndex);
}
