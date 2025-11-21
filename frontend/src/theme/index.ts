import { createSystem, defaultConfig, defineConfig } from "@chakra-ui/react";

const config = defineConfig({
  theme: {
    tokens: {
      colors: {
        // Core brand palette
        brand: {
          terracotta: { value: "#C8553D" },
          terracottaLight: { value: "#D4745F" },
          terracottaDark: { value: "#A3432F" },
          honey: { value: "#F2C078" },
          honeyLight: { value: "#F5D09A" },
          honeyDark: { value: "#E5A84E" },
          teal: { value: "#588B8B" },
          tealLight: { value: "#7AACAC" },
          tealDark: { value: "#3D6B6B" },
          linen: { value: "#FAF0E6" },
          linenDark: { value: "#F0E0CE" },
          espresso: { value: "#2C1810" },
          espressoLight: { value: "#4A3228" },
        },
        // Algorithm-specific colors (for charts and timeline)
        algo: {
          popularity: { value: "#C8553D" }, // terracotta
          contentBased: { value: "#588B8B" }, // teal
          collaborative: { value: "#F2C078" }, // honey
          hybrid: { value: "#8B5CF6" }, // purple
        },
      },
      fonts: {
        heading: { value: "'Playfair Display', serif" },
        body: { value: "'Inter', sans-serif" },
      },
    },
  },
});

export const system = createSystem(defaultConfig, config);
