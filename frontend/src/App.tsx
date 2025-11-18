import { Box, Heading, Text } from "@chakra-ui/react";

function App() {
  return (
    <Box
      minH="100vh"
      bg="brand.linen"
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
    >
      <Heading as="h1" size="4xl" color="brand.terracotta">
        ColdStart Café
      </Heading>
      <Text mt={4} fontSize="xl" color="brand.espresso">
        Experience the cold-start problem, one signal at a time.
      </Text>
    </Box>
  );
}

export default App;
