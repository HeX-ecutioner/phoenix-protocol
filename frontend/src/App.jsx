import React from 'react';
import { BrowserRouter, Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { UploadPage } from './pages/UploadPage';
import { DashboardPage } from './pages/DashboardPage';
import { DevicePage } from './pages/DevicePage';
import { AboutPage } from './pages/AboutPage';
import { PolicyPage } from './pages/PolicyPage';
import './styles/app.css';

function AnimatedRoutes() {
  const location = useLocation();
  
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<UploadPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/cookies" element={<PolicyPage type="cookies" />} />
        <Route path="/terms" element={<PolicyPage type="terms" />} />
        <Route path="/privacy" element={<PolicyPage type="privacy" />} />
        <Route path="/scans/:scanId" element={<DashboardPage />} />
        <Route path="/scans/:scanId/devices/:deviceId" element={<DevicePage />} />
      </Routes>
    </AnimatePresence>
  );
}

function RefreshRedirect() {
  const navigate = useNavigate();
  const location = useLocation();

  React.useEffect(() => {
    try {
      const navEntries = performance.getEntriesByType('navigation');
      const isReload = navEntries.length > 0 && navEntries[0].type === 'reload';
      if (isReload && location.pathname !== '/') {
        navigate('/', { replace: true, state: { showLoader: true } });
      }
    } catch {
      // Ignore if performance API is not available
    }
  }, []);

  return null;
}

function ScrollToTop() {
  const { pathname, hash } = useLocation();

  React.useEffect(() => {
    if (!hash) {
      window.scrollTo(0, 0);
    }
  }, [pathname, hash]);

  return null;
}

function App() {
  return (
    <BrowserRouter>
      <RefreshRedirect />
      <ScrollToTop />
      <AnimatedRoutes />
    </BrowserRouter>
  );
}

export default App;
