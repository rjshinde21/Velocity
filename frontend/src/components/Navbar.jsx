import React, { useState } from "react";
import velocitylogo from "../assets/velocitylogo.png";
import { Link } from "react-router-dom";
import ScrollAnchor from "./ScrollAnchor";
import { UserRound } from "lucide-react";
import LaunchlistModal from "./Launchlist";

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
    howItWorks: howItWorksRef,
    pricing: pricingRef,
    built: builtRef,
    carousel: carouselRef,
  };
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div>
      <nav className="bg-transparent text-primary fixed w-full top-0 start-0 px-6 z-20">
        <div className="max-w-screen-xl flex items-center justify-between lg:mx-auto pt-5 sm:pt-12">
          <Link to="/" className="flex items-center">
            <img src={velocitylogo} className="h-10 sm:h-14" alt="Velocity Logo" />
          </Link>

          {/* Desktop ScrollAnchor */}
          <div className="hidden sm:flex">
            <ScrollAnchor scrollRefs={scrollRefs} />
          </div>

          {/* Mobile View: Direct Buttons */}
      <div className="sm:hidden flex items-center gap-4">
        <button
          className="text-primary hover:text-blue-500 transition-colors text-sm"
          onClick={() => setIsModalOpen(true)}
        >
          Join Launchlist
        </button>

        {!isLoggedIn ? (
          <Link to="/register">
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

          {/* Desktop View Buttons */}
          <div className="hidden sm:flex items-center gap-4 sm:gap-6">
            <button
              className="text-primary hover:text-blue-500 transition-colors text-base sm:text-xl hidden sm:block"
              onClick={() => setIsModalOpen(true)}
            >
              Join Launchlist
            </button>

            {!isLoggedIn ? (
              <Link to="/register">
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
        <LaunchlistModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
      </nav>
    </div>
  );
};

export default Navbar;
