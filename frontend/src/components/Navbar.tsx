import { Box, Flex, Heading, HStack } from "@chakra-ui/react";
import { Link, useLocation } from "react-router-dom";

const navLinks = [
  { to: "/", label: "Home" },
  { to: "/simulate", label: "Simulate" },
  { to: "/challenge", label: "Challenge" },
];

export default function Navbar() {
  const location = useLocation();

  return (
    <Box
      as="nav"
      bg="brand.linen"
      borderBottomWidth="1px"
      borderColor="brand.honey"
      px={6}
      py={3}
    >
      <Flex maxW="1400px" mx="auto" align="center" justify="space-between">
        <Heading as="h1" size="lg" color="brand.terracotta">
          <Link to="/" style={{ textDecoration: "none", color: "inherit" }}>
            ☕ ColdStart Café
          </Link>
        </Heading>

        <HStack gap={6}>
          {navLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              style={{
                textDecoration: "none",
                color: location.pathname === link.to ? "#C8553D" : "#2C1810",
                fontWeight: location.pathname === link.to ? 600 : 400,
              }}
            >
              {link.label}
            </Link>
          ))}
        </HStack>
      </Flex>
    </Box>
  );
}
