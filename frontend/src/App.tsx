import { Box } from "@chakra-ui/react";
import { Route, Routes } from "react-router-dom";

import Navbar from "./components/Navbar";
import { Toaster } from "./components/Toaster";
import ChallengePage from "./pages/ChallengePage";
import LandingPage from "./pages/LandingPage";
import SimulationDashboard from "./pages/SimulationDashboard";

function App() {
  return (
    <Box minH="100vh" bg="brand.linen">
      <Navbar />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/simulate" element={<SimulationDashboard />} />
        <Route path="/challenge" element={<ChallengePage />} />
      </Routes>
      <Toaster />
    </Box>
  );
}

export default App;
