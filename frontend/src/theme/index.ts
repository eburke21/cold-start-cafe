import { createSystem, defaultConfig, defineConfig } from "@chakra-ui/react";

const config = defineConfig({
  theme: {
    tokens: {
      colors: {
        brand: {
          terracotta: { value: "#C8553D" },
          honey: { value: "#F2C078" },
          teal: { value: "#588B8B" },
          linen: { value: "#FAF0E6" },
          espresso: { value: "#2C1810" },
        },
      },
    },
  },
});

export const system = createSystem(defaultConfig, config);
