import React, { useState, useRef, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./components/Home";
// import FreeTrial from "./components/FreeTrial";
// import Pricing from "./components/PricingSection/Pricing";
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
import BuiltFor from "./components/BuiltFor";

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
  useEffect(() => {
    // Check for active session when app loads
    const checkSession = async () => {
      try {
        // Check Supabase session for Google auth
        const { data: { session } } = await supabase.auth.getSession();
        // Check localStorage for regular auth
        const storedToken = localStorage.getItem('token');
        const storedUserId = localStorage.getItem('userId');
  
        // Set logged in if either auth method is valid
        if ((session && session.user) || (storedToken && storedUserId)) {
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
        // Only clear Supabase-related data
        const token = localStorage.getItem('token');
        const userId = localStorage.getItem('userId');
        
        // If there's no regular auth data, then log out completely
        if (!token || !userId) {
          setIsLoggedIn(false);
          localStorage.clear();
        }
      }
    });
  
    return () => {
      subscription?.unsubscribe();
    };
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
  // const freeTrialRef = useRef(null);
  const pricingRef = useRef(null);
  const carouselRef = useRef(null);
  const built = useRef(null)

  const SESSION_DURATION = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

  // Session check function
  const checkSessionValidity = () => {
    const loginTime = localStorage.getItem('loginTime');
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
  
    if (!loginTime || !token || !userId) {
      return false;
    }
  
    const currentTime = new Date().getTime();
    const sessionStartTime = parseInt(loginTime, 10);
  
    return currentTime - sessionStartTime <= SESSION_DURATION;
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
    if (!isLoggedIn) return;
  
    let sessionCheckInterval;
    
    // Function to update login time
    const updateLoginTime = () => {
      localStorage.setItem('loginTime', new Date().getTime().toString());
    };
  
    // Set initial login time if not exists
    if (!localStorage.getItem('loginTime')) {
      updateLoginTime();
    }
  
    // Activity listeners
    const activityEvents = ['mousedown', 'keydown', 'scroll', 'mousemove', 'touchstart'];
    
    const handleActivity = () => {
      if (checkSessionValidity()) {
        updateLoginTime(); // Only update if session is still valid
      } else {
        handleSessionExpiration();
      }
    };
  
    // Add activity listeners
    activityEvents.forEach(event => {
      window.addEventListener(event, handleActivity);
    });
  
    // Set up session check interval
    sessionCheckInterval = setInterval(() => {
      if (!checkSessionValidity()) {
        handleSessionExpiration();
      }
    }, 60000); // Check every minute instead of every 5 seconds
  
    // Cleanup function
    return () => {
      // Remove activity listeners
      activityEvents.forEach(event => {
        window.removeEventListener(event, handleActivity);
      });
      
      // Clear interval
      if (sessionCheckInterval) {
        clearInterval(sessionCheckInterval);
      }
    };
  }, [isLoggedIn]); // Only depend on isLoggedIn
  


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
          // freeTrialRef={freeTrialRef}
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
                 <div ref={built}>
                <BuiltFor />
                </div>
                {/* <div ref={pricingRef}>
                  <Pricing isLoggedIn={isLoggedIn} />
                </div> */}
                {/* <div ref={freeTrialRef}>
                  <FreeTrial />
                </div> */}
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
