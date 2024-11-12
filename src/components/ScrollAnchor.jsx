import React, { useState } from "react";

const ScrollAnchor = () => {
  const [selected, setSelected] = useState(null);

  const handleClick = (index) => {
    setSelected(index);
  };

  return (
    <div className="flex justify-center items-center space-x-7 backdrop-blur-sm border border-[#1E1E1E] p-4 rounded-full w-fit mx-auto">
      <button
        className={`flex items-center transition text-lg ${
          selected === 1 ? "text-white" : "text-gray-500"
        }`}
        onClick={() => handleClick(1)}
      >
        <span
          className={`w-2 h-2 rounded-full mr-2 ${
            selected === 1 ? "bg-[#008ACB]" : "bg-gray-500"
          }`}
        ></span>
        Generate
      </button>

      <button
        className={`flex items-center transition text-lg ${
          selected === 2 ? "text-white" : "text-gray-500"
        }`}
        onClick={() => handleClick(2)}
      >
        <span
          className={`w-2 h-2 rounded-full mr-2 ${
            selected === 2 ? "bg-[#008ACB]" : "bg-gray-500"
          }`}
        ></span>
        Generate
      </button>

      <button
        className={`flex items-center transition text-lg ${
          selected === 3 ? "text-white" : "text-gray-500"
        }`}
        onClick={() => handleClick(3)}
      >
        <span
          className={`w-2 h-2 rounded-full mr-2 ${
            selected === 3 ? "bg-[#008ACB]" : "bg-gray-500"
          }`}
        ></span>
        Generate
      </button>
    </div>
  );
};

export default ScrollAnchor;
