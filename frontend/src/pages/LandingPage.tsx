import {
  Box,
  Button,
  Flex,
  Heading,
  HStack,
  SimpleGrid,
  Text,
  VStack,
} from "@chakra-ui/react";
import { useNavigate } from "react-router-dom";

const algorithms = [
  {
    name: "Popularity",
    color: "algo.popularity",
    hex: "#C8553D",
    description: "Recommends what everyone loves — no personalization at all.",
  },
  {
    name: "Content-Based",
    color: "algo.contentBased",
    hex: "#588B8B",
    description: "Matches movie features (genres) to your stated preferences.",
  },
  {
    name: "Collaborative",
    color: "algo.collaborative",
    hex: "#F2C078",
    description: "Finds users like you and recommends what they enjoyed.",
  },
  {
    name: "Hybrid",
    color: "algo.hybrid",
    hex: "#8B5CF6",
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
        {/* Decorative café storefront SVG */}
        <CafeStorefront />

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

        <HStack gap={4}>
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
          <Button
            size="lg"
            bg="brand.teal"
            color="white"
            px={10}
            py={6}
            fontSize="lg"
            borderRadius="full"
            _hover={{ bg: "brand.tealDark" }}
            onClick={() => navigate("/challenge")}
          >
            Challenge Mode
          </Button>
        </HStack>
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
                className="cafe-card"
              >
                <Flex align="center" gap={2} mb={2}>
                  <Box
                    w="10px"
                    h="10px"
                    borderRadius="full"
                    bg={algo.hex}
                    flexShrink={0}
                  />
                  <Heading
                    as="h4"
                    size="md"
                    color={algo.color}
                    fontFamily="heading"
                  >
                    {algo.name}
                  </Heading>
                </Flex>
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

/** Simple hand-drawn style café storefront SVG */
function CafeStorefront() {
  return (
    <svg
      width="120"
      height="100"
      viewBox="0 0 120 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Illustration of a café storefront"
      role="img"
    >
      {/* Awning */}
      <path
        d="M10 35 L60 15 L110 35"
        stroke="#C8553D"
        strokeWidth="3"
        strokeLinecap="round"
        fill="none"
      />
      <path
        d="M10 35 Q25 50 40 35 Q50 50 60 35 Q70 50 80 35 Q95 50 110 35"
        stroke="#C8553D"
        strokeWidth="2.5"
        fill="#C8553D"
        fillOpacity="0.15"
        strokeLinecap="round"
      />
      {/* Building */}
      <rect x="15" y="35" width="90" height="55" rx="2" fill="#FAF0E6" stroke="#4A3228" strokeWidth="1.5" />
      {/* Door */}
      <rect x="45" y="55" width="30" height="35" rx="3" fill="#F0E0CE" stroke="#4A3228" strokeWidth="1.5" />
      <circle cx="70" cy="73" r="2" fill="#C8553D" />
      {/* Window left */}
      <rect x="22" y="45" width="18" height="18" rx="2" fill="#588B8B" fillOpacity="0.2" stroke="#4A3228" strokeWidth="1" />
      <line x1="31" y1="45" x2="31" y2="63" stroke="#4A3228" strokeWidth="0.8" />
      <line x1="22" y1="54" x2="40" y2="54" stroke="#4A3228" strokeWidth="0.8" />
      {/* Window right */}
      <rect x="80" y="45" width="18" height="18" rx="2" fill="#588B8B" fillOpacity="0.2" stroke="#4A3228" strokeWidth="1" />
      <line x1="89" y1="45" x2="89" y2="63" stroke="#4A3228" strokeWidth="0.8" />
      <line x1="80" y1="54" x2="98" y2="54" stroke="#4A3228" strokeWidth="0.8" />
      {/* Steam from chimney */}
      <path d="M90 15 Q93 10 90 5" stroke="#C8553D" strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.5" />
      <path d="M95 18 Q98 12 95 7" stroke="#C8553D" strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.35" />
    </svg>
  );
}
