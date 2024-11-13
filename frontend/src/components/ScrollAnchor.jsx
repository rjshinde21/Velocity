import React, { useState } from "react";

const ScrollAnchor = ({ howItWorksRef, freeTrialRef, pricingRef, carouselRef }) => {
  const [selected, setSelected] = useState(null);

  const navigationItems = [
    {
      id: 1,
      label: "How it works",
      ref: howItWorksRef,
    },
    {
      id: 2,
      label: "Free Trial",
      ref: freeTrialRef,
    },
    {
      id: 3,
      label: "Pricing",
      ref: pricingRef,
    },
    {
      id: 4,
      label: "Gallery",
      ref: carouselRef,
    },
  ];

  const handleClick = (index, ref) => {
    setSelected(index);
    if (ref && ref.current) {
      ref.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  return (
    <div className="justify-center items-center sm:space-x-0 lg:space-x-7 bg-black/50 backdrop-blur-sm border border-[#1E1E1E] px-4 py-3 rounded-full w-fit mx-auto hidden sm:flex">
      {navigationItems.map((item) => (
        <button
          key={item.id}
          className={`flex items-center transition-all duration-300 text-lg px-2 py-1 rounded-3xl ${
            selected === item.id ? "text-white bg-gray-800 " : "text-gray-400"
          }`}
          onClick={() => handleClick(item.id, item.ref)}
        >
          <span
            className={`w-2 h-2 rounded-full mr-2 ${
              selected === item.id ? "bg-[#008ACB]" : "bg-gray-500"
            }`}
          />
          {item.label}
        </button>
      ))}
    </div>
  );
};

export default ScrollAnchor;