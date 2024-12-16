import React, { useState, useRef, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate,useLocation } from 'react-router-dom';
import AppContent from './components/AppContent';
import Analytics from './config/analytics';

const PageTracker = () => {
  const location = useLocation();

  useEffect(() => {
    // Track page views with more detailed information
    Analytics.track('Page View', {
      path: location.pathname,
      search: location.search,
      hash: location.hash,
      full_url: window.location.href
    });
  }, [location]);

  return null; // This component doesn't render anything
};

function App() {
  return (
    <Router basename="/">
      <PageTracker />
      <main className="bg-primary overflow-hidden scrollbar scrollbar-thumb-slate-50 scrollbar-track-slate-800">
        <AppContent />
       
      </main>
    </Router>
  );
}

export default App;
