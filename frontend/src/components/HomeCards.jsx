import React from 'react';
import cardbg from "../assets/howitworkscard.png";
import Vec1 from "../assets/vec1.png";
import Vec2 from "../assets/vec2.png";

const HomeCards = () => {
  const cardsData = [
    {
      icon: Vec1,
      title: "Customizable Prompt Templates",
      description: "Start with a base template and tweak it to fit your unique needs, ensuring every AI-generated result is tailored just right",
    },
    {
      icon: Vec2,
      title: "AI-Powered Suggestions",
      description: "Get smart, real-time suggestions to enhance your prompts, making it easy to explore new ideas and perspectives",
    },
  ];

  return (
    <div className="w-full px-4 md:px-6 font-[Inter] lg:px-8 pt-24 sm:pt-28 md:pt-32 lg:pt-36 py-8 sm:py-12 md:py-16 lg:py-20">
      <div className="flex flex-col lg:flex-row justify-center items-center gap-6 md:gap-8 lg:gap-10 
                    py-12 sm:py-16 md:py-20 lg:py-24">
        {cardsData.map((card, index) => (
          <div
            key={index}
            className="w-full max-w-[320px] sm:max-w-[400px] md:max-w-[480px] lg:max-w-[530px] 
                    min-h-[200px] sm:min-h-[220px] md:min-h-[240px] lg:min-h-[260px]
                    flex flex-col justify-center
                    p-6 sm:p-8 md:p-10
                    text-white bg-cover bg-center rounded-lg shadow-lg
                    transform transition-transform duration-300 hover:scale-[1.02]"
            style={{ 
              backgroundImage: `url(${cardbg})`,
              backgroundSize: "100% 100%",
              backgroundRepeat: "no-repeat"
            }}
          >
            <div className="flex flex-col justify-center text-left space-y-3 md:space-y-4">
            <img 
                  src={card.icon}
                  alt=""
                  className="w-6 h-6 sm:w-8 sm:h-8 md:w-10 md:h-10 lg:w-14 lg:h-14 object-contain ml-6"
                />
              <div className="font-semibold flex items-center gap-3">
                
                <span className="text-base sm:text-lg md:text-xl lg:text-2xl">
                  {card.title}
                </span>
              </div>
              <p className="text-sm sm:text-base md:text-lg lg:text-xl text-[#999999] text-left leading-relaxed">
                {card.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default HomeCards;