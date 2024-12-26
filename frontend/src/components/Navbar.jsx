import React, { useState, useEffect } from "react";
import velocitylogo from "../assets/velocitylogo.png";
import { Link } from "react-router-dom";
import ScrollAnchor from "./ScrollAnchor";
import { UserRound } from "lucide-react";
import LaunchlistModal from "./Launchlist";
import Analytics from "../config/analytics";

const Navbar = ({
  homeRef,
  howItWorksRef,
  pricingRef,
  builtRef,
  carouselRef,
  isLoggedIn,
}) => {
  const scrollRefs = {
    home: homeRef,
    howItWorksRef: howItWorksRef,
    pricing: pricingRef,
    built: builtRef,
    carousel: carouselRef,
  };

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [hasUserInteracted, setHasUserInteracted] = useState(false);
  const [hasJoinedLaunchlist, setHasJoinedLaunchlist] = useState(false);

  // Check localStorage on mount and whenever modal closes
  const checkLaunchlistStatus = () => {
    const hasJoined = localStorage.getItem('hasJoinedLaunchlist') === 'true';
    setHasJoinedLaunchlist(hasJoined);
  };

  useEffect(() => {
    checkLaunchlistStatus();
    
    // Only set the timer if user hasn't interacted and hasn't joined
    if (!hasUserInteracted && !hasJoinedLaunchlist) {
      const timer = setTimeout(() => {
        setIsModalOpen(true);
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, [hasUserInteracted, hasJoinedLaunchlist]);

  const handleManualModalOpen = () => {
    setHasUserInteracted(true);
    setIsModalOpen(true);
    Analytics.track('Button Clicked', {
      buttonName: 'Launchlist'
    });
  };

  const handleModalClose = () => {
    setHasUserInteracted(true);
    setIsModalOpen(false);
    checkLaunchlistStatus(); // Check status when modal closes
  };

  // Callback for successful registration
  const handleSuccessfulJoin = () => {
    setHasJoinedLaunchlist(true);
  };

  return (
    <div>
      <nav className="bg-transparent text-primary fixed w-full top-0 start-0 px-6 z-20">
        <div className="max-w-screen-xl flex items-center justify-between lg:mx-auto pt-5 sm:pt-12">
          <Link to="/" className="flex items-center">
            <img src={velocitylogo} className="h-10 sm:h-14" alt="Velocity Logo" />
          </Link>

          <div className="hidden sm:flex">
            <ScrollAnchor scrollRefs={scrollRefs} />
          </div>

          {/* Mobile View */}
          <div className="sm:hidden flex items-center gap-4">
            {!hasJoinedLaunchlist && (
              <button
                className="text-primary hover:text-blue-500 transition-colors text-sm"
                onClick={handleManualModalOpen}
              >
                Join Launchlist
              </button>
            )}

            {!isLoggedIn ? (
              <Link to="/login">
                <button className="rounded-full bg-black text-white py-2 px-4">
                  Get Started
                </button>
              </Link>
            ) : (
              <Link to="/profile">
                <UserRound className="border rounded-full w-8 h-8" />
              </Link>
            )}
          </div>

          {/* Desktop View */}
          <div className="hidden sm:flex items-center gap-4 sm:gap-6">
            {!hasJoinedLaunchlist && (
              <button
                className="text-primary hover:text-blue-500 transition-colors text-base sm:text-xl hidden sm:block"
                onClick={handleManualModalOpen}
              >
                Join Launchlist
              </button>
            )}

            {!isLoggedIn ? (
              <Link to="/login">
                <button className="navbtn rounded-[30px] bg-[#0a0a0a] py-[10px] sm:py-[16px] flex items-center hover:shadow-[0_0_7px_rgba(255,255,255,0.7)] transition-all duration-200">
                  <div className="inner rounded-[30px]">
                    <span className="relative z-10 bg-black px-5 sm:px-9 py-[12px] sm:py-[18px] rounded-[30px] text-lg text-white whitespace-nowrap">
                      Get Started
                    </span>
                  </div>
                </button>
              </Link>
            ) : (
              <Link to="/profile">
                <UserRound className="border rounded-full w-8 h-8 sm:w-10 sm:h-10" />
              </Link>
            )}
          </div>
        </div>
        <LaunchlistModal 
          isOpen={isModalOpen} 
          onClose={handleModalClose}
          onSuccessfulJoin={handleSuccessfulJoin}
        />
      </nav>
    </div>
  );
};

export default Navbar;