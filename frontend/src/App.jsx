import React, { useState, useRef, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./components/Home";
import FreeTrial from "./components/FreeTrial";
import Pricing from "./components/PricingSection/Pricing";
import Carousel from "./components/Carousel";
import Login from "./components/Login";
import Register from "./components/Register";
import TokenDetails from "./components/TokenDetails";
import Footer from "./components/Footer";
import HowItWorks from "./components/HowItWorks";
import ProfilePage from "./components/ProfilePage";

function App() {
  const [showLogin, setShowLogin] = useState(false);
  const [showTokenDetails, setShowTokenDetails] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    // Check for login status from localStorage
    const userId = localStorage.getItem("userId");
    const authToken = localStorage.getItem("token");
    setIsLoggedIn(!!userId && !!authToken);
  }, [isLoggedIn]);

  // Define refs for each section
  const howItWorksRef = useRef(null);
  const freeTrialRef = useRef(null);
  const pricingRef = useRef(null);
  const carouselRef = useRef(null);

  const SESSION_DURATION = 60 * 1000; // 1 minute in milliseconds

  // Session check function
  const checkSessionValidity = () => {
    const loginTime = localStorage.getItem('loginTime');
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');

    if (!loginTime || !token || !userId) {
      handleSessionExpiration();
      return false;
    }

    const currentTime = new Date().getTime();
    const sessionStartTime = parseInt(loginTime, 10);

    if (currentTime - sessionStartTime > SESSION_DURATION) {
      handleSessionExpiration();
      return false;
    }

    return true;
  };

  // Handle session expiration
  const handleSessionExpiration = () => {
    localStorage.clear();
    setIsLoggedIn(false);
    setShowTokenDetails(false);
    // window.location.href = '/login';
  };

  // Update session timestamp on user activity
  const updateSessionTimestamp = () => {
    if (isLoggedIn) {
      localStorage.setItem('loginTime', new Date().getTime().toString());
    }
  };

  useEffect(() => {
    // Initial session check
    setIsLoggedIn(checkSessionValidity());

    // Set up periodic session checks
    const sessionCheckInterval = setInterval(() => {
      setIsLoggedIn(checkSessionValidity());
    }); // Check every 10 seconds

    // Activity listeners to reset session timer
    const activityEvents = ['mousedown', 'keydown', 'scroll', 'mousemove', 'touchstart'];
    activityEvents.forEach(event => {
      window.addEventListener(event, updateSessionTimestamp);
    });

    return () => {
      clearInterval(sessionCheckInterval);
      activityEvents.forEach(event => {
        window.removeEventListener(event, updateSessionTimestamp);
      });
    };
  }, []);

  // Protected Route component
  const ProtectedRoute = ({ children }) => {
    if (!isLoggedIn) {
      return <Navigate to="/login" replace />;
    }
    return children;
  };

  const handleClick = () => {
    setShowLogin(prev => !prev);
  };

  return (
    <Router>
      <main className="bg-primary overflow-hidden scrollbar scrollbar-thumb-slate-50 scrollbar-track-slate-800">
        <Navbar
          handleClick={handleClick}
          howItWorksRef={howItWorksRef}
          freeTrialRef={freeTrialRef}
          pricingRef={pricingRef}
          carouselRef={carouselRef}
          isLoggedIn={isLoggedIn}
        />
        <Routes>
          <Route path="/profile" element={<ProfilePage />} />
          <Route
            path="/"
            element={
              <>
                <Home />
                {showLogin && !showTokenDetails && (
                  <Register setShowTokenDetails={setShowTokenDetails} />
                )}
                {showTokenDetails && <ProfilePage />}

                <div ref={howItWorksRef}>
                  <HowItWorks />
                </div>
                <div ref={freeTrialRef}>
                  <FreeTrial />
                </div>
                <div ref={pricingRef}>
                  <Pricing isLoggedIn={isLoggedIn} />
                </div>
                <div ref={carouselRef}>
                  <Carousel />
                </div>
              </>
            }
          />
          <Route path="/login" element={<Login setIsLoggedIn={setIsLoggedIn} />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
        </Routes>
        <Footer />
      </main>
    </Router>
  );
}

export default App;
