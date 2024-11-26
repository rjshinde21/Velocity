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
import PrivacyPolicy from "./components/PrivacyPolicy";
import TermsConditions from "./components/TermsConditions";
import supabase from './config/supabaseClient';

function App() {
  const [showLogin, setShowLogin] = useState(false);
  const [showTokenDetails, setShowTokenDetails] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    // Set up global auth state listener
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      console.log('Global Auth Event:', event);
      if (event === 'SIGNED_OUT') {
        // Clear local storage on sign out
        localStorage.clear();
        setIsLoggedIn(false);
      }
    });
  
    return () => {
      subscription?.unsubscribe();
    };
  }, []);
  
  // useEffect(() => {
  //   // Check for login status from localStorage
  //   const userId = localStorage.getItem("userId");
  //   const authToken = localStorage.getItem("token");
  //   setIsLoggedIn(!!userId && !!authToken);
  // }, [isLoggedIn]);
  useEffect(() => {
    // Check for active session when app loads
    const checkSession = async () => {
      try {
        // Check both Supabase session and local storage
        const { data: { session } } = await supabase.auth.getSession();
        const storedToken = localStorage.getItem('token');
        const storedUserId = localStorage.getItem('userId');

        if (session && storedToken && storedUserId) {
          setIsLoggedIn(true);
        }
      } catch (error) {
        console.error('Session check error:', error);
      } finally {
        setLoading(false);
      }
    };

    checkSession();

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      console.log('Auth state changed:', event);
      
      if (event === 'SIGNED_IN') {
        setIsLoggedIn(true);
      } else if (event === 'SIGNED_OUT') {
        setIsLoggedIn(false);
        localStorage.clear();
      }
    });

    return () => {
      subscription?.unsubscribe();
    };
  }, []);
  useEffect(() => {
    const checkSessionTimeout = () => {
      const loginTime = localStorage.getItem('loginTime');
      if (loginTime) {
        const currentTime = new Date().getTime();
        const sessionDuration = 60 * 60 * 1000; // 1 hour in milliseconds
        
        if (currentTime - parseInt(loginTime) > sessionDuration) {
          // Session expired
          console.log("session experied");
          setIsLoggedIn(false);
          localStorage.clear();
        }
      }
    };

    const interval = setInterval(checkSessionTimeout, 1000); // Check every second

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const updateLoginTime = () => {
      if (isLoggedIn) {
        localStorage.setItem('loginTime', new Date().getTime().toString());
      }
    };

    // Update time on user activity
    window.addEventListener('mousemove', updateLoginTime);
    window.addEventListener('keydown', updateLoginTime);
    window.addEventListener('click', updateLoginTime);
    window.addEventListener('scroll', updateLoginTime);

    return () => {
      window.removeEventListener('mousemove', updateLoginTime);
      window.removeEventListener('keydown', updateLoginTime);
      window.removeEventListener('click', updateLoginTime);
      window.removeEventListener('scroll', updateLoginTime);
    };
  }, [isLoggedIn]);




  // Define refs for each section
  const howItWorksRef = useRef(null);
  const freeTrialRef = useRef(null);
  const pricingRef = useRef(null);
  const carouselRef = useRef(null);

  const SESSION_DURATION = 86400 * 1000; //1 day in milli seconds

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
    console.log("Handling session expiration");
    localStorage.clear();
    setIsLoggedIn(false);
    setUser(null);
  };
  const checkLocalStorage = () => {
    const items = {
      token: localStorage.getItem('token'),
      userId: localStorage.getItem('userId'),
      loginTime: localStorage.getItem('loginTime'),
      user: localStorage.getItem('user')
    };
    console.log("Current localStorage items:", items);
    return items;
  };
  useEffect(() => {
    const storageCheck = setInterval(() => {
      checkLocalStorage();
    }, 5000); // Check every 5 seconds

    return () => clearInterval(storageCheck);
  }, []);

  // Update session timestamp on user activity
  const updateSessionTimestamp = () => {
    if (isLoggedIn) {
      localStorage.setItem('loginTime', new Date().getTime().toString());
    }
  };

  useEffect(() => {
    // Set up activity listeners
    const activityEvents = ['mousedown', 'keydown', 'scroll', 'mousemove', 'touchstart'];
    activityEvents.forEach(event => {
      window.addEventListener(event, updateSessionTimestamp);
    });

    // Session check interval
    const sessionCheckInterval = setInterval(() => {
      const currentTime = new Date().getTime();
      const loginTime = parseInt(localStorage.getItem('loginTime'), 10);

      if (!loginTime || currentTime - loginTime > SESSION_DURATION) {
        handleSessionExpiration();
      }
    }, 5000); // Check every 5 seconds

    return () => {
      activityEvents.forEach(event => {
        window.removeEventListener(event, updateSessionTimestamp);
      });
      clearInterval(sessionCheckInterval);
    };
  }, [isLoggedIn]);


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
  if (loading) {
    return <div>Loading...</div>; // Or your loading component
  }

  return (
    <Router>
      <main className="bg-primary overflow-hidden scrollbar scrollbar-thumb-slate-50 scrollbar-track-slate-800">
        {/* <Navbar
          handleClick={handleClick}
          howItWorksRef={howItWorksRef}
          freeTrialRef={freeTrialRef}
          pricingRef={pricingRef}
          carouselRef={carouselRef}
          isLoggedIn={isLoggedIn}
        /> */}
        <Routes>
          <Route path="/profile" element={<ProfilePage />} />
          <Route
            path="/"
            element={
              <>
               <Navbar
          handleClick={handleClick}
          howItWorksRef={howItWorksRef}
          freeTrialRef={freeTrialRef}
          pricingRef={pricingRef}
          carouselRef={carouselRef}
          isLoggedIn={isLoggedIn}
        />
                <Home />
                {showLogin && !showTokenDetails && (
                  <Register setShowTokenDetails={setShowTokenDetails} />
                )}
                {showTokenDetails && <ProfilePage />}

                <div ref={howItWorksRef}>
                  <HowItWorks />
                </div>
                <div ref={pricingRef}>
                  <Pricing isLoggedIn={isLoggedIn} />
                </div>
                <div ref={freeTrialRef}>
                  <FreeTrial />
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
                <ProfilePage pricingRef={pricingRef}/>
              </ProtectedRoute>
            }
          />
        <Route path="/privacypolicy" element={<PrivacyPolicy />} />
        <Route path="/terms-and-conditions" element={<TermsConditions />} />
        </Routes>
        <Footer />
      </main>
    </Router>
  );
}

export default App;
