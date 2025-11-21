import { useState } from "react";
import {
  Accordion,
  Badge,
  Box,
  Button,
  Flex,
  Heading,
  Input,
  NativeSelect,
  Text,
  VStack,
  Wrap,
} from "@chakra-ui/react";

import type { Demographics } from "../types/simulation";

/** MovieLens 100K occupations */
const OCCUPATIONS = [
  "administrator",
  "artist",
  "doctor",
  "educator",
  "engineer",
  "entertainment",
  "executive",
  "healthcare",
  "homemaker",
  "lawyer",
  "librarian",
  "marketing",
  "none",
  "other",
  "programmer",
  "retired",
  "salesman",
  "scientist",
  "student",
  "technician",
  "writer",
];

/** MovieLens 100K genres */
const ALL_GENRES = [
  "Action",
  "Adventure",
  "Animation",
  "Children's",
  "Comedy",
  "Crime",
  "Documentary",
  "Drama",
  "Fantasy",
  "Film-Noir",
  "Horror",
  "Musical",
  "Mystery",
  "Romance",
  "Sci-Fi",
  "Thriller",
  "War",
  "Western",
];

interface SignalPanelProps {
  ratingsCount: number;
  hasDemographics: boolean;
  genrePreferences: string[];
  viewHistoryCount: number;
  isLoading: boolean;
  onOpenRatingModal: () => void;
  onOpenViewHistoryModal: () => void;
  onSetDemographics: (demographics: Demographics) => Promise<void>;
  onSetGenrePreferences: (genres: string[]) => Promise<void>;
}

export default function SignalPanel({
  ratingsCount,
  hasDemographics,
  genrePreferences,
  viewHistoryCount,
  isLoading,
  onOpenRatingModal,
  onOpenViewHistoryModal,
  onSetDemographics,
  onSetGenrePreferences,
}: SignalPanelProps) {
  // Demographics form state
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("");
  const [occupation, setOccupation] = useState("");

  // Genre selection state
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);

  const handleDemographicsSubmit = () => {
    const demographics: Demographics = {
      age: age ? parseInt(age, 10) : null,
      gender: gender || null,
      occupation: occupation || null,
    };
    // Must have at least one field
    if (!demographics.age && !demographics.gender && !demographics.occupation) {
      return;
    }
    onSetDemographics(demographics);
  };

  const toggleGenre = (genre: string) => {
    setSelectedGenres((prev) =>
      prev.includes(genre) ? prev.filter((g) => g !== genre) : [...prev, genre],
    );
  };

  const handleGenreSubmit = () => {
    if (selectedGenres.length === 0) return;
    onSetGenrePreferences(selectedGenres);
  };

  return (
    <Box>
      <Heading
        as="h3"
        size="sm"
        color="brand.espresso"
        mb={4}
        fontFamily="heading"
      >
        Add Signals
      </Heading>

      <Accordion.Root multiple defaultValue={["rating"]}>
        {/* 1. Rate a Movie */}
        <Accordion.Item value="rating">
          <Accordion.ItemTrigger cursor="pointer" py={3}>
            <Flex flex="1" justify="space-between" align="center">
              <Text fontWeight="500" fontSize="sm">
                Rate a Movie
              </Text>
              {ratingsCount > 0 && (
                <Badge bg="brand.terracotta" color="white" borderRadius="full">
                  {ratingsCount}
                </Badge>
              )}
            </Flex>
          </Accordion.ItemTrigger>
          <Accordion.ItemContent pb={4}>
            <Button
              size="sm"
              w="100%"
              bg="brand.teal"
              color="white"
              _hover={{ bg: "brand.tealDark" }}
              onClick={onOpenRatingModal}
              disabled={isLoading}
            >
              Search & Rate
            </Button>
          </Accordion.ItemContent>
        </Accordion.Item>

        {/* 2. Set Demographics */}
        <Accordion.Item value="demographics">
          <Accordion.ItemTrigger cursor="pointer" py={3}>
            <Flex flex="1" justify="space-between" align="center">
              <Text fontWeight="500" fontSize="sm">
                Demographics
              </Text>
              {hasDemographics && (
                <Badge bg="brand.teal" color="white" borderRadius="full">
                  Set
                </Badge>
              )}
            </Flex>
          </Accordion.ItemTrigger>
          <Accordion.ItemContent pb={4}>
            <VStack gap={3} align="stretch">
              <Box>
                <Text fontSize="xs" fontWeight="500" mb={1}>
                  Age
                </Text>
                <Input
                  type="number"
                  placeholder="e.g. 25"
                  size="sm"
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                  min={1}
                  max={120}
                  disabled={hasDemographics}
                />
              </Box>
              <Box>
                <Text fontSize="xs" fontWeight="500" mb={1}>
                  Gender
                </Text>
                <NativeSelect.Root size="sm" disabled={hasDemographics}>
                  <NativeSelect.Field
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                  >
                    <option value="">Select...</option>
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                  </NativeSelect.Field>
                </NativeSelect.Root>
              </Box>
              <Box>
                <Text fontSize="xs" fontWeight="500" mb={1}>
                  Occupation
                </Text>
                <NativeSelect.Root size="sm" disabled={hasDemographics}>
                  <NativeSelect.Field
                    value={occupation}
                    onChange={(e) => setOccupation(e.target.value)}
                  >
                    <option value="">Select...</option>
                    {OCCUPATIONS.map((occ) => (
                      <option key={occ} value={occ}>
                        {occ.charAt(0).toUpperCase() + occ.slice(1)}
                      </option>
                    ))}
                  </NativeSelect.Field>
                </NativeSelect.Root>
              </Box>
              <Button
                size="sm"
                bg="brand.teal"
                color="white"
                _hover={{ bg: "brand.tealDark" }}
                onClick={handleDemographicsSubmit}
                disabled={isLoading || hasDemographics}
              >
                {hasDemographics ? "Demographics Set" : "Submit Demographics"}
              </Button>
            </VStack>
          </Accordion.ItemContent>
        </Accordion.Item>

        {/* 3. Genre Preferences */}
        <Accordion.Item value="genres">
          <Accordion.ItemTrigger cursor="pointer" py={3}>
            <Flex flex="1" justify="space-between" align="center">
              <Text fontWeight="500" fontSize="sm">
                Genre Preferences
              </Text>
              {genrePreferences.length > 0 && (
                <Badge bg="brand.honey" color="brand.espresso" borderRadius="full">
                  {genrePreferences.length}
                </Badge>
              )}
            </Flex>
          </Accordion.ItemTrigger>
          <Accordion.ItemContent pb={4}>
            <VStack gap={3} align="stretch">
              <Wrap gap={2}>
                {ALL_GENRES.map((genre) => (
                  <Button
                    key={genre}
                    size="xs"
                    borderRadius="full"
                    variant={selectedGenres.includes(genre) ? "solid" : "outline"}
                    bg={
                      selectedGenres.includes(genre)
                        ? "brand.honey"
                        : "transparent"
                    }
                    color={
                      selectedGenres.includes(genre)
                        ? "brand.espresso"
                        : "brand.espressoLight"
                    }
                    borderColor="brand.linenDark"
                    _hover={{
                      bg: selectedGenres.includes(genre)
                        ? "brand.honeyDark"
                        : "brand.linenDark",
                    }}
                    onClick={() => toggleGenre(genre)}
                    disabled={isLoading}
                  >
                    {genre}
                  </Button>
                ))}
              </Wrap>
              <Button
                size="sm"
                bg="brand.teal"
                color="white"
                _hover={{ bg: "brand.tealDark" }}
                onClick={handleGenreSubmit}
                disabled={isLoading || selectedGenres.length === 0}
              >
                Apply ({selectedGenres.length} selected)
              </Button>
            </VStack>
          </Accordion.ItemContent>
        </Accordion.Item>

        {/* 4. View History */}
        <Accordion.Item value="viewHistory">
          <Accordion.ItemTrigger cursor="pointer" py={3}>
            <Flex flex="1" justify="space-between" align="center">
              <Text fontWeight="500" fontSize="sm">
                View History
              </Text>
              {viewHistoryCount > 0 && (
                <Badge bg="brand.teal" color="white" borderRadius="full">
                  {viewHistoryCount}
                </Badge>
              )}
            </Flex>
          </Accordion.ItemTrigger>
          <Accordion.ItemContent pb={4}>
            <Button
              size="sm"
              w="100%"
              bg="brand.teal"
              color="white"
              _hover={{ bg: "brand.tealDark" }}
              onClick={onOpenViewHistoryModal}
              disabled={isLoading}
            >
              Browse & Add Movies
            </Button>
          </Accordion.ItemContent>
        </Accordion.Item>
      </Accordion.Root>
    </Box>
  );
}
