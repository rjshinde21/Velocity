import React from "react";
import star from "../assets/Home/star.png";
import HomeCards from "./HomeCards";
import { Link } from "react-router-dom";

const Home = () => {
  return (
    <>
      <div className="absolute left-20 top-0 h-full w-[2px] bg-gradient-to-b from-[#1E1E1E] to-[#6ACFFF] opacity-20 hidden sm:block" />

      <div className="absolute right-20 top-0 h-full w-[2px] bg-gradient-to-b from-[#1E1E1E] to-[#6ACFFF] opacity-20 hidden sm:block" />


      <div className="relative flex items-center justify-center flex-col pt-72 bg-gradient-to-b from-transparent to-[#000000]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_#008ACB_0%,_transparent_40%)] opacity-30 animate-gradient-move" />
        <div className="absolute inset-0 bg-black opacity-0 flex" />

        <div className="relative z-10 flex flex-col items-center justify-center">
          <h1 className="font-[Amenti] bg-gradient-text pt-30 text-3xl sm:text-6xl mb-4">
            Unlock Infinite Creativity
          </h1>
          <p className="text-[#999999] font-[Inter] text-sm sm:text-lg">
            Generate Your Perfect AI Prompts!
          </p>
          <Link to="/profile">
          <button className="glowing-button flex items-center gap-2 sm:mt-12 mt-6">
            <span>Try Now</span>
            <img src={star} alt="Star" />
          </button>
          </Link>
        </div>
        <HomeCards />
      <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent via-[12%] bottom-0" />
      </div>
    </>
  );
};

export default Home;
