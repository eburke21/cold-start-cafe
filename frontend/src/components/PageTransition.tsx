import type { ReactNode } from "react";
import { motion } from "framer-motion";

interface PageTransitionProps {
  children: ReactNode;
}

/**
 * Wraps a page component with a fade + slide-up entrance animation.
 *
 * Used with `AnimatePresence` in App.tsx to animate route transitions.
 * The animation creates a subtle "entering the café" feeling:
 * - Fade in from 0 → 1 opacity
 * - Slide up from 10px → 0 translateY
 * - 300ms duration with easeOut easing
 */
export default function PageTransition({ children }: PageTransitionProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
}
