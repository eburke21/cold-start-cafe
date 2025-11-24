/**
 * Challenge results: horizontal grouped bar chart comparing user vs. algorithms.
 *
 * Uses Recharts BarChart to show precision@10 for the user and each algorithm.
 * Win/loss badges indicate which algorithms the user beat.
 * Café-themed flavor text adds personality to the results.
 */

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Badge, Box, Flex, HStack, Text, VStack } from "@chakra-ui/react";

import type { AlgorithmScore, MetricScores } from "../types/challenge";

/** Algorithm display colors — matches the simulation chart palette. */
const ALGO_COLORS: Record<string, string> = {
  popularity: "#C8553D",
  content_based: "#588B8B",
  collaborative: "#F2C078",
  hybrid: "#8B5CF6",
};

/** User gets a warm gold color to stand out. */
const USER_COLOR = "#D4A017";

/** Friendly display names for algorithms. */
const ALGO_LABELS: Record<string, string> = {
  popularity: "Popularity",
  content_based: "Content-Based",
  collaborative: "Collaborative",
  hybrid: "Hybrid",
};

interface ScoreComparisonProps {
  userScore: MetricScores;
  algoScores: AlgorithmScore[];
}

export default function ScoreComparison({
  userScore,
  algoScores,
}: ScoreComparisonProps) {
  // Build Recharts data: one row per scorer (user + each algo)
  const chartData = [
    {
      name: "You",
      precision: userScore.precision_at_10,
      fill: USER_COLOR,
    },
    ...algoScores.map((s) => ({
      name: ALGO_LABELS[s.algorithm] || s.algorithm,
      precision: s.precision_at_10,
      fill: ALGO_COLORS[s.algorithm] || "#999",
    })),
  ];

  // Count wins
  const wins = algoScores.filter(
    (s) => userScore.precision_at_10 > s.precision_at_10,
  );

  return (
    <VStack gap={4} align="stretch">
      {/* Header with win/loss summary */}
      <Box textAlign="center">
        <Text fontSize="xl" fontWeight="bold" color="brand.espresso">
          {getFlavorText(wins.length)}
        </Text>
        <Text fontSize="sm" color="brand.espressoLight" mt={1}>
          You beat {wins.length} of 4 algorithms on Precision@10
        </Text>
      </Box>

      {/* Win/loss badges */}
      <Flex justify="center" wrap="wrap" gap={2}>
        {algoScores.map((s) => {
          const userWon = userScore.precision_at_10 > s.precision_at_10;
          return (
            <Badge
              key={s.algorithm}
              bg={userWon ? "green.100" : "red.100"}
              color={userWon ? "green.700" : "red.700"}
              px={3}
              py={1}
              borderRadius="full"
              fontSize="xs"
            >
              {userWon ? "✅" : "❌"}{" "}
              {ALGO_LABELS[s.algorithm] || s.algorithm}
            </Badge>
          );
        })}
      </Flex>

      {/* Bar chart */}
      <Box bg="white" p={4} borderRadius="lg" className="cafe-card">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis
              type="number"
              domain={[0, 1]}
              tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
            />
            <YAxis type="category" dataKey="name" width={110} />
            <Tooltip
              formatter={(value) => [
                `${(Number(value) * 100).toFixed(1)}%`,
                "Precision@10",
              ]}
            />
            <Legend />
            <Bar
              dataKey="precision"
              name="Precision@10"
              radius={[0, 4, 4, 0]}
              isAnimationActive={true}
              animationDuration={800}
              animationEasing="ease-out"
            >
              {chartData.map((entry, idx) => (
                <Cell key={idx} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Box>

      {/* Detailed scores table */}
      <Box bg="white" p={4} borderRadius="lg" className="cafe-card">
        <Text fontSize="sm" fontWeight="600" color="brand.espresso" mb={2}>
          Detailed Scores
        </Text>
        <VStack gap={1} align="stretch">
          <HStack justify="space-between" py={1} borderBottomWidth="1px">
            <Text fontSize="xs" fontWeight="600" color="brand.espressoLight">
              Scorer
            </Text>
            <HStack gap={4}>
              <Text
                fontSize="xs"
                fontWeight="600"
                color="brand.espressoLight"
                w="60px"
                textAlign="right"
              >
                P@10
              </Text>
              <Text
                fontSize="xs"
                fontWeight="600"
                color="brand.espressoLight"
                w="60px"
                textAlign="right"
              >
                NDCG@10
              </Text>
            </HStack>
          </HStack>
          {/* User row */}
          <HStack justify="space-between" py={1} bg="brand.linenDark" px={2} borderRadius="md">
            <HStack gap={2}>
              <Box w="8px" h="8px" borderRadius="full" bg={USER_COLOR} />
              <Text fontSize="sm" fontWeight="600" color="brand.espresso">
                You
              </Text>
            </HStack>
            <HStack gap={4}>
              <Text fontSize="sm" w="60px" textAlign="right">
                {(userScore.precision_at_10 * 100).toFixed(1)}%
              </Text>
              <Text fontSize="sm" w="60px" textAlign="right">
                {(userScore.ndcg_at_10 * 100).toFixed(1)}%
              </Text>
            </HStack>
          </HStack>
          {/* Algorithm rows */}
          {algoScores.map((s) => (
            <HStack key={s.algorithm} justify="space-between" py={1} px={2}>
              <HStack gap={2}>
                <Box
                  w="8px"
                  h="8px"
                  borderRadius="full"
                  bg={ALGO_COLORS[s.algorithm]}
                />
                <Text fontSize="sm" color="brand.espresso">
                  {ALGO_LABELS[s.algorithm] || s.algorithm}
                </Text>
              </HStack>
              <HStack gap={4}>
                <Text fontSize="sm" w="60px" textAlign="right">
                  {(s.precision_at_10 * 100).toFixed(1)}%
                </Text>
                <Text fontSize="sm" w="60px" textAlign="right">
                  {(s.ndcg_at_10 * 100).toFixed(1)}%
                </Text>
              </HStack>
            </HStack>
          ))}
        </VStack>
      </Box>
    </VStack>
  );
}

/** Returns café-themed flavor text based on win count. */
function getFlavorText(wins: number): string {
  if (wins === 4) return "☕ You outperformed the entire house!";
  if (wins === 3) return "🏆 Almost a clean sweep — impressive taste!";
  if (wins === 2) return "👏 A solid showing at the café!";
  if (wins === 1) return "🤔 The machines had the edge today.";
  return "🤖 The regulars know this place better than you... for now!";
}
