import React from "react";

const GetStartedBtn = ({content, click}) => {

  return (
    <button onClick={click} className="navbtn rounded-[30px] bg-[#0a0a0a] py-[10px] sm:py-[16px] flex items-center hover:shadow-[0_0_7px_rgba(255,255,255,0.7)] transition-all duration-200">
      <div className="inner rounded-[30px]">
        <span className="relative z-10 bg-black px-5 sm:px-9 py-[12px] sm:py-[18px] rounded-[30px] text-lg text-white">
          {content}
        </span>
      </div>
    </button>
  );
};

export default GetStartedBtn;
