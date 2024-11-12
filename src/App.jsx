import React, { useState, useRef } from "react";
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
import HowItWorksCard from "./components/HowItWorks/HowItWorksCard";
import HowItWorks from "./components/HowItWorks/HowItWorks";
import ProfilePage from "./components/ProfilePage";

function App() {
  const [showLogin, setShowLogin] = useState(false);
  const [showTokenDetails, setShowTokenDetails] = useState(false);

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
      <main className="bg-primary overflow-hidden">
        <Navbar
          handleClick={handleClick}
          howItWorksRef={howItWorksRef}
          freeTrialRef={freeTrialRef}
          pricingRef={pricingRef}
          carouselRef={carouselRef}
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
                {showTokenDetails && <TokenDetails />}
                
                {/* Attach refs to sections */}
                <div ref={howItWorksRef}>
                  <HowItWorks />
                </div>
                <div ref={freeTrialRef}>
                  <FreeTrial />
                </div>
                <div ref={pricingRef}>
                  <Pricing />
                </div>
                <div ref={carouselRef}>
                  <Carousel />
                </div>
              </>
            }
          />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/token-details" element={<TokenDetails />} />
        </Routes>
        <Footer />
      </main>
    </Router>
  );
}

export default App;
