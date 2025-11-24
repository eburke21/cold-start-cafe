import { useState } from "react";
import { Box, HStack, Text } from "@chakra-ui/react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { AlgorithmName, SimulationStep } from "../types/simulation";

/**
 * Metric key type — the three IR metrics we track per algorithm.
 * Used to toggle which metric the chart displays.
 */
type MetricKey = "precision_at_10" | "recall_at_10" | "ndcg_at_10";

const METRIC_OPTIONS: { key: MetricKey; label: string }[] = [
  { key: "precision_at_10", label: "Precision@10" },
  { key: "recall_at_10", label: "Recall@10" },
  { key: "ndcg_at_10", label: "NDCG@10" },
];

/**
 * Algorithm display config — maps algorithm names to their colors and labels.
 * Colors are raw hex values (not theme tokens) because Recharts
 * operates outside Chakra's style system.
 */
const ALGORITHMS: {
  key: AlgorithmName;
  label: string;
  color: string;
}[] = [
  { key: "popularity", label: "Popularity", color: "#C8553D" },
  { key: "content_based", label: "Content-Based", color: "#588B8B" },
  { key: "collaborative", label: "Collaborative", color: "#F2C078" },
  { key: "hybrid", label: "Hybrid", color: "#8B5CF6" },
];

/** Row shape for Recharts — one row per step, one column per algorithm. */
interface ChartDataPoint {
  step: number;
  popularity: number;
  content_based: number;
  collaborative: number;
  hybrid: number;
}

/**
 * Transform simulation steps into Recharts-compatible wide-format data.
 * Pivots from row-per-algorithm to row-per-step with algorithm columns.
 */
function transformData(
  steps: SimulationStep[],
  metric: MetricKey,
): ChartDataPoint[] {
  return steps.map((step) => {
    const point: ChartDataPoint = {
      step: step.step_number,
      popularity: 0,
      content_based: 0,
      collaborative: 0,
      hybrid: 0,
    };
    for (const result of step.results) {
      point[result.algorithm] = result[metric];
    }
    return point;
  });
}

interface MetricsChartProps {
  steps: SimulationStep[];
}

/**
 * Line chart showing algorithm performance over simulation steps.
 *
 * Displays four colored lines (one per algorithm) with toggleable metrics.
 * Uses Recharts' built-in animation for smooth data point transitions.
 */
export default function MetricsChart({ steps }: MetricsChartProps) {
  const [activeMetric, setActiveMetric] = useState<MetricKey>("precision_at_10");
  const data = transformData(steps, activeMetric);

  return (
    <Box>
      {/* Metric toggle buttons */}
      <HStack gap={2} mb={4} role="group" aria-label="Metric selector">
        {METRIC_OPTIONS.map((option) => (
          <Box
            key={option.key}
            as="button"
            px={3}
            py={1.5}
            borderRadius="full"
            fontSize="sm"
            fontWeight={activeMetric === option.key ? "600" : "400"}
            bg={activeMetric === option.key ? "brand.terracotta" : "white"}
            color={activeMetric === option.key ? "white" : "brand.espressoLight"}
            aria-pressed={activeMetric === option.key}
            aria-label={`Show ${option.label} metric`}
            borderWidth="1px"
            borderColor={
              activeMetric === option.key ? "brand.terracotta" : "brand.linenDark"
            }
            cursor="pointer"
            _hover={{
              bg:
                activeMetric === option.key
                  ? "brand.terracottaDark"
                  : "brand.linenDark",
            }}
            transition="all 0.2s"
            onClick={() => setActiveMetric(option.key)}
          >
            {option.label}
          </Box>
        ))}
      </HStack>

      {/* Chart */}
      <Box bg="white" p={4} borderRadius="lg" className="cafe-card">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart
            data={data}
            margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#E8DDD0" />
            <XAxis
              dataKey="step"
              label={{
                value: "Step",
                position: "insideBottomRight",
                offset: -5,
                style: { fontSize: 12, fill: "#4A3228" },
              }}
              tick={{ fontSize: 12, fill: "#4A3228" }}
            />
            <YAxis
              domain={[0, 1]}
              tickCount={6}
              label={{
                value: METRIC_OPTIONS.find((m) => m.key === activeMetric)?.label,
                angle: -90,
                position: "insideLeft",
                offset: 10,
                style: { fontSize: 12, fill: "#4A3228" },
              }}
              tick={{ fontSize: 12, fill: "#4A3228" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#FAF0E6",
                border: "1px solid #E8DDD0",
                borderRadius: "8px",
                fontSize: "13px",
              }}
              formatter={(value) =>
                typeof value === "number" ? value.toFixed(3) : String(value ?? "")
              }
              labelFormatter={(label) => `Step ${label}`}
            />
            <Legend
              wrapperStyle={{ fontSize: "13px", paddingTop: "8px" }}
            />
            {ALGORITHMS.map((algo) => (
              <Line
                key={algo.key}
                type="monotone"
                dataKey={algo.key}
                name={algo.label}
                stroke={algo.color}
                strokeWidth={2.5}
                dot={{ r: 4, fill: algo.color }}
                activeDot={{ r: 6 }}
                isAnimationActive={true}
                animationDuration={600}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>

        {steps.length === 0 && (
          <Text
            textAlign="center"
            color="brand.espressoLight"
            fontStyle="italic"
            mt={-4}
          >
            Add signals to see algorithm performance
          </Text>
        )}
      </Box>

      {/* Screen reader data table — hidden visually, available to assistive tech */}
      {data.length > 0 && (
        <Box srOnly>
          <table>
            <caption>
              {METRIC_OPTIONS.find((m) => m.key === activeMetric)?.label} by
              algorithm across simulation steps
            </caption>
            <thead>
              <tr>
                <th>Step</th>
                {ALGORITHMS.map((a) => (
                  <th key={a.key}>{a.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <tr key={row.step}>
                  <td>{row.step}</td>
                  {ALGORITHMS.map((a) => (
                    <td key={a.key}>{row[a.key].toFixed(3)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </Box>
      )}
    </Box>
  );
}
