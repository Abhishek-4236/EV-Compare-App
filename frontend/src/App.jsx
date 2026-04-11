import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import BrowsePage from './pages/BrowsePage';
import ComparePage from './pages/ComparePage';
import VehicleDetailPage from './pages/VehicleDetailPage';
import ChatPage from './pages/ChatPage';
import StationsPage from './pages/StationsPage';
import RecommendPage from './pages/RecommendPage';
import SubsidiesPage from './pages/SubsidiesPage';

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 1000 * 60 * 5, retry: 1 } }
});

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -6 }}
        transition={{ duration: 0.2 }}
      >
        <Routes location={location}>
          <Route path="/" element={<HomePage />} />
          <Route path="/browse" element={<BrowsePage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/vehicle/:id" element={<VehicleDetailPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/stations" element={<StationsPage />} />
          <Route path="/recommend" element={<RecommendPage />} />
          <Route path="/subsidies" element={<SubsidiesPage />} />
          <Route path="*" element={<HomePage />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Navbar />
        <AnimatedRoutes />
      </Router>
    </QueryClientProvider>
  );
}

export default App;