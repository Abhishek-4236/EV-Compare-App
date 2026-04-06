import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import BrowsePage from './pages/BrowsePage';
import ComparePage from './pages/ComparePage';
import VehicleDetailPage from './pages/VehicleDetailPage';
import RecommendPage from './pages/RecommendPage';
import ChatPage from './pages/ChatPage';  // add import

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/browse" element={<BrowsePage />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/vehicle/:id" element={<VehicleDetailPage />} />
        <Route path="/recommend" element={<RecommendPage />} />
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </Router>
  );
}

export default App;