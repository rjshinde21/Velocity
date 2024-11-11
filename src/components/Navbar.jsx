import React from "react";
import velocitylogo from "../assets/velocitylogo.png";
import GetStartedBtn from "./GetStartedBtn";
import { Link } from "react-router-dom";
import ScrollAnchor from "./ScrollAnchor";

const Navbar = ({handleClick}) => {

  return (
    <div>
      <nav class="bg-transparent text-primary fixed z-20 w-full top-0 start-0 px-4 sm:px-5">
        <div class="max-w-screen-2xl flex flex-wrap items-center justify-between sm:mx-10 lg:mx-auto pt-5 sm:pt-12">
          <Link to="#" class="flex items-center space-x-3 w-[161px]">
            <img src={velocitylogo} class="h-10 sm:h-14" alt="Velocity Logo" />
          </Link>
          <ScrollAnchor />
          <Link to="/register">
          <GetStartedBtn click={handleClick} content="Get Started"/>
          </Link>
        </div>
      </nav>
    </div>
  );
};

export default Navbar;
