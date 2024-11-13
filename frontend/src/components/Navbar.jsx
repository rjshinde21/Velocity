import React from "react";
import velocitylogo from "../assets/velocitylogo.png";
import GetStartedBtn from "./GetStartedBtn";
import { Link } from "react-router-dom";
import ScrollAnchor from "./ScrollAnchor";

const Navbar = ({ handleClick, howItWorksRef, freeTrialRef, pricingRef, carouselRef }) => {
  return (
    <div>
      <nav className="bg-transparent text-primary fixed w-full top-0 start-0 px-4 sm:px-5 z-50">
        <div className="max-w-screen-3xl flex flex-wrap items-center justify-between sm:mx-10 lg:mx-auto pt-5 sm:pt-12">
          <Link to="/" className="flex items-center space-x-3 sm:w-auto lg:w-[161px]">
            <img src={velocitylogo} className="h-10 sm:h-14" alt="Velocity Logo" />
          </Link>

          {/* Render ScrollAnchor inside Navbar */}
          <ScrollAnchor
            howItWorksRef={howItWorksRef}
            freeTrialRef={freeTrialRef}
            pricingRef={pricingRef}
            carouselRef={carouselRef}
          />

          <Link to="/register">
            <GetStartedBtn click={handleClick} content="Get Started" />
          </Link>
        </div>
      </nav>
    </div>
  );
};

export default Navbar;
