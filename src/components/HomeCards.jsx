import React from 'react';
import cardbg from "../assets/howitworkscard.png";

const HomeCards = () => {
  // Array of card data
  const cardsData = [
    {
      title: "Customizable Prompt Templates",
      description: "Start with a base template and tweak it to fit your unique needs, ensuring every AI-generated result is tailored just right",
    },
    {
      title: "AI-Powered Suggestions",
      description: "Get smart, real-time suggestions to enhance your prompts, making it easy to explore new ideas and perspectives",
    },
  ];

  return (
    <div className="flex flex-col sm:flex-row justify-center items-center gap-6 sm:gap-10 pb-16 pt-56">
      {cardsData.map((card, index) => (
        <div
          key={index}
          className="max-w-[530px] max-h-[260px] flex flex-col justify-center items-center py-10 mx-4 px-4 sm:py-16 sm:px-10 sm:mx-0 text-white bg-cover bg-center rounded-md shadow-lg"
          style={{ backgroundImage: `url(${cardbg})`, backgroundSize: "contain",backgroundRepeat: "no-repeat" }}
        >
          <div className="flex flex-col justify-center text-left">
            <div className="font-semibold mb-5 flex items-center">
              <span className="text-lg">{card.title}</span>
            </div>
            <p className="text-lg text-[#999999] text-left">
              {card.description}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
};

export default HomeCards;
