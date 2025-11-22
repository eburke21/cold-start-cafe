import { Box } from "@chakra-ui/react";
import { AnimatePresence } from "framer-motion";
import { Route, Routes, useLocation } from "react-router-dom";

import Navbar from "./components/Navbar";
import PageTransition from "./components/PageTransition";
import { Toaster } from "./components/Toaster";
import ChallengePage from "./pages/ChallengePage";
import LandingPage from "./pages/LandingPage";
import SimulationDashboard from "./pages/SimulationDashboard";

function App() {
  const location = useLocation();

  return (
    <Box minH="100vh" bg="brand.linen">
      <Navbar />
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route
            path="/"
            element={
              <PageTransition>
                <LandingPage />
              </PageTransition>
            }
          />
          <Route
            path="/simulate"
            element={
              <PageTransition>
                <SimulationDashboard />
              </PageTransition>
            }
          />
          <Route
            path="/challenge"
            element={
              <PageTransition>
                <ChallengePage />
              </PageTransition>
            }
          />
        </Routes>
      </AnimatePresence>
      <Toaster />
    </Box>
  );
}

export default App;
