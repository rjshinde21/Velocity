import "./App.css";
import Navbar from "./components/Navbar";
import Home from "./components/Home";
import Card from "./components/Card";
import FreeTrial from "./components/FreeTrial";
import Pricing from "./components/PricingSection/Pricing";
import Carousel from "./components/Carousel";
import Login from "./components/Login";
import { useState } from "react";
import Register from "./components/Register";
import TokenDetails from "./components/TokenDetails"; // Import TokenDetails
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Footer from "./components/Footer";
import HowItWorksCard from "./components/HowItWorks/HowItWorksCard";

function App() {
  const [showLogin, setShowLogin] = useState(false);
  const [showTokenDetails, setShowTokenDetails] = useState(false); // New state

  const handleClick = () => {
    setShowLogin((prev) => !prev);
  };

  return (
    <Router>
      <main className="bg-primary overflow-hidden">
        <Navbar handleClick={handleClick} />
        <Routes>
          <Route
            path="/"
            element={
              <>
                <Home />
                {showLogin && !showTokenDetails && (
                  <Register setShowTokenDetails={setShowTokenDetails} />
                )}
                {showTokenDetails && <TokenDetails />}
                <HowItWorksCard />
                <FreeTrial />
                <Pricing />
                <Carousel speed={40000} />
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
