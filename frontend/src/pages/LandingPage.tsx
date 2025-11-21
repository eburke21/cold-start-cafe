import { Box, Button, Heading, SimpleGrid, Text, VStack } from "@chakra-ui/react";
import { useNavigate } from "react-router-dom";

const algorithms = [
  {
    name: "Popularity",
    color: "algo.popularity",
    description: "Recommends what everyone loves — no personalization at all.",
  },
  {
    name: "Content-Based",
    color: "algo.contentBased",
    description: "Matches movie features (genres) to your stated preferences.",
  },
  {
    name: "Collaborative",
    color: "algo.collaborative",
    description: "Finds users like you and recommends what they enjoyed.",
  },
  {
    name: "Hybrid",
    color: "algo.hybrid",
    description: "Blends all signals — the more data it gets, the smarter it becomes.",
  },
];

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <Box>
      {/* Hero Section */}
      <VStack
        gap={6}
        py={20}
        px={8}
        textAlign="center"
        maxW="800px"
        mx="auto"
      >
        <Heading
          as="h2"
          fontSize={{ base: "3xl", md: "5xl" }}
          color="brand.espresso"
          fontFamily="heading"
          lineHeight="1.2"
        >
          What happens when a recommendation system knows{" "}
          <Text as="span" color="brand.terracotta">
            nothing
          </Text>{" "}
          about you?
        </Heading>

        <Text
          fontSize={{ base: "lg", md: "xl" }}
          color="brand.espressoLight"
          maxW="600px"
        >
          Watch four algorithms compete in real time as you feed them signals —
          ratings, demographics, genre preferences, and viewing history. See the
          cold-start problem unfold, one signal at a time.
        </Text>

        <Button
          size="lg"
          bg="brand.terracotta"
          color="white"
          px={10}
          py={6}
          fontSize="lg"
          borderRadius="full"
          _hover={{ bg: "brand.terracottaDark" }}
          onClick={() => navigate("/simulate")}
        >
          Start a Simulation
        </Button>
      </VStack>

      {/* Algorithm Explainer Grid */}
      <Box bg="brand.linenDark" py={16} px={8}>
        <VStack gap={8} maxW="1000px" mx="auto">
          <Heading
            as="h3"
            size="xl"
            color="brand.espresso"
            fontFamily="heading"
          >
            Four Algorithms, One Race
          </Heading>

          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={6} w="100%">
            {algorithms.map((algo) => (
              <Box
                key={algo.name}
                bg="white"
                p={6}
                borderRadius="lg"
                borderTopWidth="4px"
                borderTopColor={algo.color}
                shadow="sm"
              >
                <Heading
                  as="h4"
                  size="md"
                  color={algo.color}
                  mb={2}
                  fontFamily="heading"
                >
                  {algo.name}
                </Heading>
                <Text fontSize="sm" color="brand.espressoLight">
                  {algo.description}
                </Text>
              </Box>
            ))}
          </SimpleGrid>
        </VStack>
      </Box>
    </Box>
  );
}
