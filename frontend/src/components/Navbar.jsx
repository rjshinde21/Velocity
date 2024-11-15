import React from "react";
import velocitylogo from "../assets/velocitylogo.png";
import { Link } from "react-router-dom";
import ScrollAnchor from "./ScrollAnchor";
import { UserRound } from "lucide-react";

const Navbar = ({
  handleClick,
  howItWorksRef,
  freeTrialRef,
  pricingRef,
  carouselRef,
  isLoggedIn,
}) => {
  return (
    <div>
      <nav className="bg-transparent text-primary fixed w-full top-0 start-0 px-4 sm:px-8 z-20">
        <div className="max-w-screen-3xl flex flex-wrap items-center justify-between sm:mx-10 lg:mx-auto pt-5 sm:pt-12">
          <Link
            to="/"
            className={`flex items-center space-x-3 sm:w-auto ${
              !isLoggedIn ? "lg:w-[161px]" : "w-auto"
            }`}
          >
            <img
              src={velocitylogo}
              className="h-10 sm:h-14"
              alt="Velocity Logo"
            />
          </Link>

          {/* Render ScrollAnchor inside Navbar */}
          <ScrollAnchor
            howItWorksRef={howItWorksRef}
            freeTrialRef={freeTrialRef}
            pricingRef={pricingRef}
            carouselRef={carouselRef}
          />
          {!isLoggedIn ? (
            <Link to="/register">
              <button className="navbtn rounded-[30px] bg-[#0a0a0a] py-[10px] sm:py-[16px] flex items-center hover:shadow-[0_0_7px_rgba(255,255,255,0.7)] transition-all duration-200">
                <div className="inner rounded-[30px]">
                  <span className="relative z-10 bg-black px-5 sm:px-9 py-[12px] sm:py-[18px] rounded-[30px] text-lg text-white">
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
      </nav>
    </div>
  );
};

export default Navbar;
