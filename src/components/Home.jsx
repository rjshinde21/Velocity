import React from "react";
import star from "../assets/Home/star.png";
import bg from "../assets/mainbg.png"

const Home = () => {
  return (
    <div
      className="flex flex-col items-center justify-center h-[100vh] w-[100vw]"
      style={{
        backgroundImage: `url(${bg})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      <h1 className="font-[Amenti] bg-gradient-text pt-30 text-3xl sm:text-6xl mb-4">
        Unlock Infinite Creativity
      </h1>
      <p className="text-[#999999] font-[Inter] text-sm sm:text-lg">
        Generate Your Perfect AI Prompts!
      </p>
      <button className="glowing-button flex items-center gap-2 sm:mt-12 mt-6">
        <span>Try Now</span>
        <img src={star} alt="Star" />
      </button>
    </div>
  );
};

export default Home;
