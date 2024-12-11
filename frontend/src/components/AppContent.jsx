import React, { useState, useRef, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import Navbar from "./Navbar";
import Home from "./Home";
import Carousel from "./Carousel";
import Login from "./Login";
import Register from "./Register";
import HowItWorks from "./HowItWorks";
import BuiltFor from "./BuiltFor";
import ProfilePage from "./ProfilePage";
import PrivacyPolicy from "./PrivacyPolicy";
import TermsConditions from "./TermsConditions";
import { onAuthStateChanged, setPersistence, browserLocalPersistence } from 'firebase/auth';
import { auth } from '../config/firebaseConfig';
import Footer from "./Footer";
// Separate the main app logic into a new component
function AppContent() {
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);
  
  // Define refs
  const howItWorksRef = useRef(null);
  const freeTrialRef = useRef(null);
  const pricingRef = useRef(null);
  const carouselRef = useRef(null);
  const builtRef  = useRef(null);
  const homeRef = useRef(null);

  useEffect(() => {
    const SESSION_DURATION = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
    
    const checkExistingAuth = async () => {
      const storedToken = localStorage.getItem('token');
      const authMethod = localStorage.getItem('authMethod'); // New item to track auth method
      const loginTime = localStorage.getItem('sharedLoginTime');
      
      // Check if session has expired
      if (loginTime) {
        const currentTime = new Date().getTime();
        const sessionAge = currentTime - parseInt(loginTime);
        
        if (sessionAge > SESSION_DURATION) {
          console.log('Session expired');
          await handleLogout();
          return;
        }
      }
      
      if (storedToken) {
        try {
          const verifyResponse = await fetch('https://thinkvelocity.in/api/api/users/verify-token', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${storedToken}`,
              'Content-Type': 'application/json'
            }
          });

          if (verifyResponse.ok) {
            console.log('Token verified, updating session timestamp');
            localStorage.setItem('sharedLoginTime', new Date().getTime().toString());
            setIsLoggedIn(true);
          } else {
            console.log('Token verification failed, logging out');
            await handleLogout();
          }
        } catch (error) {
          console.error('Token verification failed:', error);
          await handleLogout();
        }
      }
      setLoading(false);
    };

    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      console.log('Auth state changed:', user ? 'User present' : 'No user');
      
      // Only proceed with Firebase auth checks if using Google authentication
      const authMethod = localStorage.getItem('authMethod');
      if (authMethod !== 'google') {
        setLoading(false);
        return;
      }
      
      if (user) {
        try {
          const storedToken = localStorage.getItem('token');
          if (storedToken) {
            try {
              const verifyResponse = await fetch('https://thinkvelocity.in/api/api/users/verify-token', {
                method: 'POST',
                headers: {
                  'Authorization': `Bearer ${storedToken}`,
                  'Content-Type': 'application/json'
                }
              });

              if (verifyResponse.ok) {
                console.log('Token still valid, maintaining session');
                setIsLoggedIn(true);
                setLoading(false);
                return;
              }
            } catch (error) {
              console.error('Token verification failed:', error);
            }
          }

          // Rest of your existing Google auth logic...
        } catch (error) {
          console.error('Auth processing error:', error);
          await handleLogout();
        }
      } else {
        // Only handle logout for Google auth
        const hasStoredAuth = localStorage.getItem('token') && 
                            localStorage.getItem('userId') &&
                            localStorage.getItem('authMethod') === 'google';
        if (hasStoredAuth && isLoggedIn) {
          await handleLogout();
        }
      }
      setLoading(false);
    });

    // Check existing auth on mount
    checkExistingAuth();

    return () => unsubscribe();
  }, [navigate, isLoggedIn]);
 

  const handleLogout = async () => {
    console.log('Handling logout...');
    
    const keysToRemove = [
      'token',
      'userId',
      'userEmail',
      'userName',
      'sharedUser',
      'firebaseUser',
      'sharedLoginTime'
    ];
    
    keysToRemove.forEach(key => localStorage.removeItem(key));
    
    setIsLoggedIn(false);
    
    try {
      await auth.signOut();
      navigate('/login');
    } catch (error) {
      console.error('Signout error:', error);
    }
  };
  
  // Protected Route component
  const ProtectedRoute = ({ children }) => {
    const storedToken = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const userName = localStorage.getItem('userName');
    const [isAuthorized, setIsAuthorized] = useState(true); // Start with true to prevent flash
    const [isChecking, setIsChecking] = useState(true);
    const timerRef = useRef(null);
    const authMethod = localStorage.getItem('authMethod');
    useEffect(() => {
      const storedToken = localStorage.getItem('token');
      const userId = localStorage.getItem('userId');
      const authMethod = localStorage.getItem('authMethod');

      // Clear any existing timer
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }

      const checkAuth = async () => {
        if (!storedToken || !userId) {
          setIsAuthorized(false);
          setIsChecking(false);
          return;
        }

        try {
          // Only verify token for Google auth
          if (authMethod === 'google') {
            try {
              const verifyResponse = await fetch('https://thinkvelocity.in/api/api/users/verify-token', {
                method: 'POST',
                headers: {
                  'Authorization': `Bearer ${storedToken}`,
                  'Content-Type': 'application/json'
                }
              });

              if (!verifyResponse.ok) {
                setIsAuthorized(false);
                setIsChecking(false);
                return;
              }
            } catch (error) {
              console.error('Token verification failed:', error);
              setIsAuthorized(false);
              setIsChecking(false);
              return;
            }
          }

          setIsAuthorized(true);
        } catch (error) {
          console.error('Auth check failed:', error);
          setIsAuthorized(false);
        } finally {
          setIsChecking(false);
        }
      };

      // Set a minimum delay for the auth check
      timerRef.current = setTimeout(checkAuth, 100);

      return () => {
        if (timerRef.current) {
          clearTimeout(timerRef.current);
        }
      };
    }, []);
    if (isChecking) {
      return (
        <div className="flex items-center justify-center h-screen bg-black">
          <div className="text-white">Loading...</div>
        </div>
      );
    }


    if (!isAuthorized) {
      return <Navigate to="/login" replace />;
    }
    return children;
  };
  
  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <>
      <Routes>
        <Route
          path="/"
          element={
            <>
              <Navbar
                howItWorksRef={howItWorksRef}
                homeRef={homeRef}
                // freeTrialRef={freeTrialRef}
                carouselRef={carouselRef}
                builtRef={builtRef}
                isLoggedIn={isLoggedIn}
              />
              {/* <Home /> */}
              <div ref={homeRef}><Home /></div>
              <div ref={howItWorksRef}><HowItWorks /></div>
              <div ref={builtRef}><BuiltFor /></div>
              <div ref={carouselRef}><Carousel /></div>
              <Footer />
            </>
          }
        />
        <Route 
          path="/login" 
          element={
            <>
              {/* <Navbar isLoggedIn={isLoggedIn} /> */}
              <Login setIsLoggedIn={setIsLoggedIn} />
        
            </>
          } 
        />
        <Route 
          path="/register" 
          element={
            <>
              {/* <Navbar isLoggedIn={isLoggedIn} /> */}
              <Register />
            </>
          } 
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <ProfilePage pricingRef={pricingRef}/>
            </ProtectedRoute>
            
          }
        />
        <Route 
          path="/privacypolicy" 
          element={
            <>
              <Navbar isLoggedIn={isLoggedIn} />
              <PrivacyPolicy />
            </>
          } 
        />
        <Route 
          path="/terms-and-conditions" 
          element={
            <>
              <Navbar isLoggedIn={isLoggedIn} />
              <TermsConditions />
            </>
          } 
        />
        {/* Catch-all route for unknown paths */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

export default AppContent;
