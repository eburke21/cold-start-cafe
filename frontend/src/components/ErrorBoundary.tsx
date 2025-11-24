/**
 * React error boundary — catches rendering errors and shows a
 * friendly recovery UI instead of a white screen.
 *
 * Uses class component because React error boundaries require
 * getDerivedStateFromError / componentDidCatch lifecycle methods
 * (no hook equivalent exists).
 */

import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { Box, Button, Heading, Text, VStack } from "@chakra-ui/react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box minH="100vh" bg="brand.linen" display="flex" alignItems="center" justifyContent="center">
          <VStack gap={6} textAlign="center" maxW="500px" px={8}>
            <Text fontSize="5xl">☕</Text>
            <Heading
              as="h2"
              size="xl"
              color="brand.espresso"
              fontFamily="heading"
            >
              Something went wrong
            </Heading>
            <Text color="brand.espressoLight" fontSize="md">
              The café hit an unexpected snag. Try reloading the page — if
              the problem persists, the barista is working on it.
            </Text>
            {this.state.error && (
              <Text
                fontSize="xs"
                color="brand.espressoLight"
                fontFamily="mono"
                bg="brand.linenDark"
                p={3}
                borderRadius="md"
                maxW="100%"
                overflowX="auto"
              >
                {this.state.error.message}
              </Text>
            )}
            <Button
              bg="brand.terracotta"
              color="white"
              _hover={{ bg: "brand.terracottaDark" }}
              onClick={() => window.location.reload()}
            >
              Reload Page
            </Button>
          </VStack>
        </Box>
      );
    }

    return this.props.children;
  }
}
