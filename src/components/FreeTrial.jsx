import React from "react";
import { Link } from "react-router-dom";

const FreeTrial = () => {
  return (
    <div class="w-[70%] flex flex-col sm:flex-row justify-between items-center mx-auto px-6 py-10 sm:px-16 sm:py-24 gap-8 bg-gradient-to-b from-[#121212] to-[#040404] rounded-lg mt-12 mb-28">
      <div className="flex flex-col gap-7">
        <span class="text-2xl sm:text-5xl font-semibold font-[Inter] bg-gradient-text bg-clip-text text-transparent">
          7 - Day Free Trial!
        </span>
        <span class="font-[Inter] text-md sm:text-xl bg-gradient-text bg-clip-text text-transparent leading-relaxed">
          No commitment, just creative <br /> exploration. Start your trial
          today!
        </span>
      </div>
      <Link to="/register">
      <button className="flex text-lg px-7 py-3 sm:px-14 sm:py-5 text-primary rounded-[35px] items-center shadow-[0_0_15px_rgba(255,255,255,0.7)]">
        Get Started
      </button>
      </Link>
    </div>
  );
};

export default FreeTrial;
