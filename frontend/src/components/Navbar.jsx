import React, { useEffect, useState } from "react";
import velocitylogo from "../assets/velocitylogo.png";
import GetStartedBtn from "./GetStartedBtn";
import { Link } from "react-router-dom";
import ScrollAnchor from "./ScrollAnchor";
import { UserRound } from "lucide-react";

const Navbar = ({
  handleClick,
  howItWorksRef,
  freeTrialRef,
  pricingRef,
  carouselRef
}) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    // Check for login status from localStorage
    const userId = localStorage.getItem("userId");
    const authToken = localStorage.getItem("token");
    setIsLoggedIn(!!userId && !!authToken);
  }, [isLoggedIn]);

  return (
    <div>
      <nav className="bg-transparent text-primary fixed w-full top-0 start-0 px-4 sm:px-8 z-10">
        <div className="max-w-screen-3xl flex flex-wrap items-center justify-between sm:mx-10 lg:mx-auto pt-5 sm:pt-12">
          <Link
            to="/"
            className={`flex items-center space-x-3 sm:w-auto ${!isLoggedIn ? 'lg:w-[161px]' : 'w-auto'}`}
          >
            <img
              src={velocitylogo}
              className="h-10 sm:h-14"
              alt="Velocity Logo"
            />
          </Link>

          <ScrollAnchor
            howItWorksRef={howItWorksRef}
            freeTrialRef={freeTrialRef}
            pricingRef={pricingRef}
            carouselRef={carouselRef}
          />
          {!isLoggedIn ? (
            <Link to="/register">
              <GetStartedBtn click={handleClick} content="Get Started" />
            </Link>
          ) : (
            <Link to="/profile">
              <UserRound className="border rounded-full w-8 h-8 sm:w-10 sm:h-10"/>
            </Link>
          )}
        </div>
      </nav>
    </div>
  );
};

export default Navbar;
