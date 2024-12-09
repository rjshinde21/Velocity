import React from "react";

const GetStartedBtn = ({ content, click }) => {
  return (
    <button
      onClick={click}
      className="group relative rounded-[30px] bg-[#0a0a0a] py-[10px] sm:py-[16px] transition-all duration-200 hover:shadow-[0_0_7px_rgba(255,255,255,0.7)]"
      type="button"
    >
      <div className="relative rounded-[30px] overflow-hidden">
        <span className="block relative z-10 bg-black px-5 sm:px-9 py-[12px] sm:py-[18px] rounded-[30px] text-lg text-white">
          {content}
        </span>
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-blue-400 opacity-0 group-hover:opacity-10 transition-opacity duration-200"></div>
      </div>
    </button>
  );
};

export default GetStartedBtn;