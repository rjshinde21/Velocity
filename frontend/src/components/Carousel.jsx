import React, { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const testimonials = [
  {
    id: 1,
    name: "Shrishti Munjal",
    role: "CEO Zetoupe",
    image: "/api/placeholder/80/80",
    testimonial: "Velocity feels like having a creative partner who just gets you. It takes the guesswork out of crafting prompts, saving me hours and delivering spot-on results. Intuitive, smooth, and a total game-changer for anyone working with AI!"
  },
  {
    id: 2,
    name: "Alex Chen",
    role: "Creative Director",
    image: "/api/placeholder/80/80",
    testimonial: "The AI prompt suggestions have revolutionized our creative workflow. What used to take hours now takes minutes. Absolutely incredible tool!"
  },
  {
    id: 3,
    name: "Sarah Johnson",
    role: "Content Strategist",
    image: "/api/placeholder/80/80",
    testimonial: "The interface is intuitive and the results are consistently impressive. It's become an indispensable part of our content creation process."
  }
];

const Carousel = () => {
  const [currentIndex, setCurrentIndex] = useState(0);

  const handlePrevious = () => {
    setCurrentIndex((prev) => (prev === 0 ? testimonials.length - 1 : prev - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev === testimonials.length - 1 ? 0 : prev + 1));
  };

  return (
    <div className="relative min-h-[600px] lg:min-h-[800px] w-full">
      {/* Background Image Container */}
      <div 
        className="absolute inset-0 bg-center bg-cover opacity-50"
        style={{
          backgroundImage: "url('https://toteminteractive.in/velosty/mask.png')",
        }}
      />
      
      {/* Dark Overlay */}
      <div className="absolute inset-0 bg-black/40" />

      {/* Content Container */}
      <div className="relative h-full w-full max-w-6xl mx-auto px-4 flex flex-col justify-center items-center">
        {/* Title */}
        <h2 className="text-center text-2xl sm:text-3xl font-[Amenti] mb-12 text-white">
          What our creators say
        </h2>

        {/* Carousel Container */}
        <div className="relative w-full max-w-3xl">
          {/* Navigation Buttons */}
          <button
            onClick={handlePrevious}
            className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 sm:-translate-x-8 z-10 bg-black/50 hover:bg-black/75 text-white rounded-full p-2 transition-colors"
            aria-label="Previous testimonial"
          >
            <ChevronLeft size={24} />
          </button>
          <button
            onClick={handleNext}
            className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 sm:translate-x-8 z-10 bg-black/50 hover:bg-black/75 text-white rounded-full p-2 transition-colors"
            aria-label="Next testimonial"
          >
            <ChevronRight size={24} />
          </button>

          {/* Testimonial Card */}
          <div className="bg-[#121212] rounded-[32px] p-8 sm:p-10 mx-auto shadow-lg backdrop-blur-sm bg-opacity-95">
            <div className="flex flex-col sm:flex-row items-start gap-6">
              {/* Profile Image */}
              <div className="w-16 h-16 rounded-full overflow-hidden flex-shrink-0">
                <img
                  src={testimonials[currentIndex].image}
                  alt={testimonials[currentIndex].name}
                  className="w-full h-full object-cover"
                />
              </div>

              {/* Content */}
              <div className="flex-1 space-y-3">
                <div className="space-y-1">
                  <h3 className="text-2xl font-light text-white">
                    {testimonials[currentIndex].name}
                  </h3>
                  <p className="text-gray-500 text-sm">
                    {testimonials[currentIndex].role}
                  </p>
                </div>
                <p className="text-gray-400 leading-relaxed">
                  {testimonials[currentIndex].testimonial}
                </p>
              </div>
            </div>
          </div>

          {/* Progress Indicators */}
          <div className="flex justify-center items-center gap-3 mt-8">
            {testimonials.map((_, index) => (
              <div
                key={index}
                className={`h-[2px] rounded-full transition-all duration-300 ${
                  index === currentIndex ? 'w-12 bg-white' : 'w-6 bg-gray-600'
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Carousel;