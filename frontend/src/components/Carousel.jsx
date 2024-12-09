import React, { useState, useRef, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import img1 from "../assets/carousel1.png";
import img2 from "../assets/carousel2.png";
import img3 from "../assets/carousel3.png";
import img4 from "../assets/carousel4.png";
import img5 from "../assets/carousel5.png";
import img6 from "../assets/carousel6.png";
import img7 from "../assets/carousel7.png";
import img8 from "../assets/carousel8.png";
import img9 from "../assets/carousel9.png";
import img10 from "../assets/carousel10.png";
import img11 from "../assets/carousel11.png";
import img12 from "../assets/carousel12.png";
import girl from "../assets/girl_img.png";
import grid1 from "../assets/grid.png";

const Carousel = ({ speed = 30000 }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  
  const generateUniqueId = () => {
    return '_' + Math.random().toString(36).substr(2, 9);
  };

  const images = [
    img1, img2, img3, img4, img5, img6,
    img7, img8, img9, img10, img11, img12
  ].map((image) => ({
    id: generateUniqueId(),
    image,
  }));

  // Double the images array for seamless loop
  const duplicatedImages = [...images, ...images];

  const testimonials = [
    {
      id: 1,
      name: "Shrishti Munjal",
      role: "CEO Zetoupe",
      image: girl,
      testimonial: "Velocity feels like having a creative partner who just gets you. It takes the guesswork out of crafting prompts, saving me hours and delivering spot-on results. Intuitive, smooth"
    },
    {
      id: 2,
      name: "Alex Chen",
      role: "Creative Director",
      image: girl,
      testimonial: "The AI prompt suggestions have revolutionized our creative workflow. What used to take hours now takes minutes. Absolutely incredible tool!"
    },
    {
      id: 3,
      name: "Sarah Johnson",
      role: "Content Strategist",
      image: girl,
      testimonial: "The interface is intuitive and the results are consistently impressive. It's become an indispensable part of our content creation process."
    }
  ];

  const handlePrevious = () => {
    setCurrentIndex((prev) => (prev === 0 ? testimonials.length - 1 : prev - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev === testimonials.length - 1 ? 0 : prev + 1));
  };

  return (
    <div className="w-full">
      <div
        className="bg-black grid place-items-center p-8 relative"
        style={{
          backgroundImage: `url(${grid1})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
          height: "100%",
          width: "100%",
        }}
      >
  <div className="relative min-h-[400px] md:min-h-[300px] lg:min-h-[200px] w-full">
    {/* Background Image Container */}
    <div 
      className="absolute inset-0 bg-center bg-cover opacity-50"
      style={{
        backgroundImage: "url('https://toteminteractive.in/velosty/mask.png')",
      }}
    />
    
    <div className="absolute inset-0 bg-black/40" />

    <div className="relative h-full w-full max-w-6xl mx-auto px-4 md:px-6 lg:px-8 flex flex-col justify-center items-center py-8 md:py-12">
      <h2 className="text-center text-xl md:text-2xl lg:text-3xl font-[Amenti] mb-6 md:mb-8 lg:mb-12 text-white">
        What our creators say
      </h2>

      <div className="relative w-full max-w-3xl">
        <button
          onClick={handlePrevious}
          className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-2 md:-translate-x-4 lg:-translate-x-8 z-10 bg-black/50 hover:bg-black/75 text-white rounded-full p-1.5 md:p-2 transition-colors"
          aria-label="Previous testimonial"
        >
          <ChevronLeft size={20} className="w-4 h-4 md:w-6 md:h-6" />
        </button>
        <button
          onClick={handleNext}
          className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-2 md:translate-x-4 lg:translate-x-8 z-10 bg-black/50 hover:bg-black/75 text-white rounded-full p-1.5 md:p-2 transition-colors"
          aria-label="Next testimonial"
        >
          <ChevronRight size={20} className="w-4 h-4 md:w-6 md:h-6" />
        </button>

        <div className="bg-[#121212] rounded-2xl md:rounded-[32px] p-4 sm:p-6 md:p-8 lg:p-10 mx-auto shadow-lg backdrop-blur-sm bg-opacity-95 w-full sm:w-[80%] md:w-[70%] lg:w-[60%]">
          <div className="flex flex-col sm:flex-row items-start gap-4 md:gap-6">
            <div className="w-12 h-12 md:w-16 md:h-16 rounded-full overflow-hidden flex-shrink-0">
              <img
                src={testimonials[currentIndex].image}
                alt={testimonials[currentIndex].name}
                className="w-full h-full object-cover"
              />
            </div>

            <div className="flex-1 space-y-2 md:space-y-3">
              <div className="space-y-0.5 md:space-y-1">
                <h3 className="text-xl md:text-2xl font-light text-white">
                  {testimonials[currentIndex].name}
                </h3>
                <p className="text-gray-500 text-xs md:text-sm">
                  {testimonials[currentIndex].role}
                </p>
              </div>
              <p className="text-gray-400 text-sm md:text-base leading-relaxed">
                {testimonials[currentIndex].testimonial}
              </p>
            </div>
          </div>
        </div>

        <div className="flex justify-center items-center gap-2 md:gap-3 mt-4 md:mt-8">
          {testimonials.map((_, index) => (
            <div
              key={index}
              className={`h-[2px] rounded-full transition-all duration-300 ${
                index === currentIndex ? 'w-8 md:w-12 bg-white' : 'w-4 md:w-6 bg-gray-600'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  </div>
  </div>

  <div className="w-full px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
    <h1 className="bg-gradient-text py-4 sm:py-6 md:py-10 lg:py-20 text-lg sm:text-xl md:text-2xl lg:text-4xl mb-4 sm:mb-6 md:mb-8 lg:mb-12 text-left font-[Amenti] sm:ml-0 lg:ml-16">
      At Velocity — We craft AI-driven prompts <br className="hidden sm:block" /> that engage your audience
      with clarity <br className="hidden sm:block" /> and creativity.
    </h1>
  </div>


  {/* Backward scrolling section */}
  <div className="inner1 overflow-hidden px-4">
        <div className="wrapper row1 flex gap-4">
          <section
            className="flex gap-4"
            style={{ "--speed": `${speed}ms`, width: "100%" }}
          >
            {images.map(({ id, image }) => (
              <div className="image flex-shrink-0" key={id}>
                <img src={image} alt={id} className="w-full h-auto" />
              </div>
            ))}
          </section>
        </div>
      </div>

      {/* Forward scrolling section */}
      <div className="inner1 overflow-hidden px-4 mt-4">
        <div className="wrapper row2 flex gap-4">
          <section
            className="flex gap-4"
            style={{ "--speed": `${speed}ms`, width: "100%" }}
          >
            {images.map(({ id, image }) => (
              <div className="image flex-shrink-0" key={id}>
                <img src={image} alt={id} className="w-full h-auto" />
              </div>
            ))}
          </section>
        </div>
      </div>
</div>
  );
};

export default Carousel;