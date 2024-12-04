import React, { useState, useRef, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./components/Home";
import Carousel from "./components/Carousel";
import Login from "./components/Login";
import Register from "./components/Register";
import TokenDetails from "./components/TokenDetails";
import Footer from "./components/Footer";
import HowItWorks from "./components/HowItWorks";
import ProfilePage from "./components/ProfilePage";
import PrivacyPolicy from "./components/PrivacyPolicy";
import TermsConditions from "./components/TermsConditions";
import { onAuthStateChanged, setPersistence, browserLocalPersistence } from 'firebase/auth';
import { auth } from './config/firebaseConfig';
import BuiltFor from './components/BuiltFor';
import AppContent from './components/AppContent';

function App() {
  return (
    <Router>
      <main className="bg-primary overflow-hidden scrollbar scrollbar-thumb-slate-50 scrollbar-track-slate-800">
        <AppContent />
        {/* <Footer /> */}
      </main>
    </Router>
  );
}

export default App;
