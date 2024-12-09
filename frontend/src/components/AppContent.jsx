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
    console.log('Initializing auth state...');
    
    const checkExistingAuth = async () => {
      const storedToken = localStorage.getItem('token');
      const storedUser = localStorage.getItem('firebaseUser');
      
      if (storedToken && storedUser) {
        try {
          // Make sure to include 'Bearer ' prefix with the token
          const verifyResponse = await fetch('https://thinkvelocity.in/api/api/users/verify-token', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${storedToken}`,
              'Content-Type': 'application/json'
            }
          });

          if (verifyResponse.ok) {
            console.log('Existing token verified successfully');
            setIsLoggedIn(true);
            return; // Add return to prevent further execution
          } else {
            console.log('Token verification failed, proceeding with logout');
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
      
      if (user) {
        try {
          // Check if we already have valid credentials first
          const storedToken = localStorage.getItem('token');
          if (storedToken) {
            try {
              const verifyResponse = await fetch('https://thinkvelocity.in/api/api/users/verify-token', {
                method: 'POST',
                headers: {
                  'Authorization': `Bearer ${storedToken}`,
                  'Content-Type': 'application/json'
                },
                // Add body with user ID if needed by your API
                body: JSON.stringify({
                  userId: localStorage.getItem('userId')
                })
              });

              if (verifyResponse.ok) {
                console.log('Token still valid, maintaining session');
                setIsLoggedIn(true);
                setLoading(false);
                return; // Stop here if token is valid
              }
            } catch (error) {
              console.error('Token verification failed:', error);
            }
          }

          // If no token or verification failed, proceed with login
          const response = await fetch('https://thinkvelocity.in/api/api/users/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              email: user.email,
              googleId: user.uid
            })
          });

          const data = await response.json();
          
          if (response.ok) {
            const authData = {
              token: data.data.token,
              user: {
                id: data.data.user.id,
                email: data.data.user.email,
                name: data.data.user.name
              },
              firebase: {
                uid: user.uid,
                email: user.email,
                displayName: user.displayName
              }
            };

            // Store all necessary data
            localStorage.setItem('token', authData.token);
            localStorage.setItem('userId', authData.user.id);
            localStorage.setItem('userEmail', authData.user.email);
            localStorage.setItem('userName', authData.user.name);
            localStorage.setItem('sharedUser', JSON.stringify(authData.user));
            localStorage.setItem('firebaseUser', JSON.stringify(authData.firebase));
            localStorage.setItem('sharedLoginTime', new Date().getTime().toString());

            console.log('Stored auth data:', {
              token: authData.token,
              userId: authData.user.id,
              userName: authData.user.name
            });

            setIsLoggedIn(true);
           // navigate('/profile');
          }
        } catch (error) {
          console.error('Auth processing error:', error);
          await handleLogout();
        }
      } else {
        // Only logout if we previously had auth data
        const hasStoredAuth = localStorage.getItem('token') && 
                            localStorage.getItem('userId');
        // if (hasStoredAuth && isLoggedIn) {
        //   await handleLogout();
        // }
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
  
    if (!storedToken || !userId || !userName || !isLoggedIn) {
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
            </>
          }
        />
        <Route 
          path="/login" 
          element={
            <>
              <Navbar isLoggedIn={isLoggedIn} />
              <Login setIsLoggedIn={setIsLoggedIn} />
            </>
          } 
        />
        <Route 
          path="/register" 
          element={
            <>
              <Navbar isLoggedIn={isLoggedIn} />
              <Register />
            </>
          } 
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              {/* <Navbar isLoggedIn={isLoggedIn} /> */}
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
