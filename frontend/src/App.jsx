import React, { useState, useRef, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
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

  const handleClick = () => {
    setShowLogin((prev) => !prev);
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
                  <Pricing isLoggedIn={isLoggedIn}/>
                </div>
                <div ref={carouselRef}>
                  <Carousel />
                </div>
              </>
            }
          />
          <Route path="/login" element={<Login setIsLoggedIn={setIsLoggedIn}/>} />
          <Route path="/register" element={<Register />} />
          <Route path="/profile" element={<ProfilePage pricingRef={pricingRef}/>} />
        </Routes>
        <Footer />
      </main>
    </Router>
  );
}

export default App;
