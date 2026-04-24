import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Suspense, lazy, useEffect } from 'react';
import Navbar from './components/Navbar';
import useAuth from './store/useAuth';
import CompareBar from './components/CompareBar';
import useCompare from './store/useCompare';

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 1000 * 60 * 5, retry: 1 } }
});
const MotionDiv = motion.div;
const HomePage = lazy(() => import('./pages/HomePage'));
const BrowsePage = lazy(() => import('./pages/BrowsePage'));
const ComparePage = lazy(() => import('./pages/ComparePage'));
const VehicleDetailPage = lazy(() => import('./pages/VehicleDetailPage'));
const ChatPage = lazy(() => import('./pages/ChatPage'));
const RecommendPage = lazy(() => import('./pages/RecommendPage'));
const SubsidiesPage = lazy(() => import('./pages/SubsidiesPage'));
const AuthPage = lazy(() => import('./pages/AuthPage'));
const TcoPage = lazy(() => import('./pages/TcoPage'));
const GaragePage = lazy(() => import('./pages/GaragePage'));
const AdminPage = lazy(() => import('./pages/AdminPage'));
const ChargingMapPage = lazy(() => import('./pages/ChargingMapPage'));

function AnimatedRoutes() {
  const location = useLocation();
  const isAuthPage = location.pathname === '/login';

  return (
    <AnimatePresence mode="wait">
      <MotionDiv
        key={location.pathname}
        className="ev-route-stage"
        initial={{ opacity: 0, y: isAuthPage ? 0 : 18, filter: 'blur(6px)', scale: isAuthPage ? 0.98 : 1 }}
        animate={{ opacity: 1, y: 0, filter: 'blur(0px)', scale: 1 }}
        exit={{ opacity: 0, y: isAuthPage ? 0 : -10, filter: 'blur(4px)', scale: isAuthPage ? 0.98 : 1 }}
        transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
      >
        <Suspense fallback={<div className="page-shell-loading">Loading...</div>}>
          <Routes location={location}>
            <Route path="/" element={<HomePage />} />
            <Route path="/browse" element={<BrowsePage />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="/vehicle/:id" element={<VehicleDetailPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/recommend" element={<RecommendPage />} />
            <Route path="/subsidies" element={<SubsidiesPage />} />
            <Route path="/tco" element={<TcoPage />} />
            <Route path="/garage" element={<GaragePage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/map" element={<ChargingMapPage />} />
            <Route path="/login" element={<AuthPage />} />
            <Route path="/signup" element={<AuthPage />} />
            <Route path="*" element={<HomePage />} />
          </Routes>
        </Suspense>
      </MotionDiv>
    </AnimatePresence>
  );
}

function AppInner() {
  const initialize = useAuth(s => s.initialize);
  const { compareItems, removeCompare, clearCompare } = useCompare();
  const location = useLocation();

  // Initialize auth session once on app load
  useEffect(() => {
    initialize();
  }, [initialize]);

  const showCompareBar = location.pathname !== '/compare' && compareItems.length > 0;

  return (
    <>
      <Navbar />
      <AnimatedRoutes />
      {showCompareBar && (
        <CompareBar
          selected={compareItems}
          onRemove={removeCompare}
          onClear={clearCompare}
        />
      )}
    </>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AppInner />
      </Router>
    </QueryClientProvider>
  );
}

export default App;
