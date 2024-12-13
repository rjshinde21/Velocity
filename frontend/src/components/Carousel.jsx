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
import arman from "../assets/arman.png";
import arjun from "../assets/s-3.jpg"
import grid1 from "../assets/bgcreators.png";

const Carousel = ({ speed = 30000 }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const touchStartX = useRef(0);
  const touchEndX = useRef(0);
  const [isDragging, setIsDragging] = useState(false);
  const [startPos, setStartPos] = useState(0);
  const [currentTranslate, setCurrentTranslate] = useState(0);
  const slideContainerRef = useRef(null);

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



  const testimonials = [
    {
      id: 1,
      name: "Aakash Puri",
      role: "CEO Totem Interactive",
      image: girl,
      testimonial: "Velocity feels like having a creative partner who just gets you. It takes the guesswork out of crafting prompts"
    },
    {
      id: 2,
      name: "Arman siddiqui",
      role: "Technical art lead",
      image: arman,
      testimonial: "The AI prompt suggestions have revolutionized our creative workflow. Absolutely incredible tool!"
    },
    {
      id: 3,
      name: "Arjun gujar",
      role: "Developer Totem Interactive",
      image: arjun,
      testimonial: "The interface is intuitive and the results are consistently impressive. It's become an indispensable part."
    }
  ];



  // Touch handlers
  const handleTouchStart = (e) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchMove = (e) => {
    touchEndX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = () => {
    const touchDiff = touchStartX.current - touchEndX.current;
    const minSwipeDistance = 50;

    if (Math.abs(touchDiff) > minSwipeDistance) {
      if (touchDiff > 0) {
        handleNext();
      } else {
        handlePrevious();
      }
    }
  };

  const handlePrevious = () => {
    setCurrentIndex((prev) => (prev === 0 ? testimonials.length - 1 : prev - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev === testimonials.length - 1 ? 0 : prev + 1));
  };

  const handleDragStart = (e) => {
    setIsDragging(true);
    setStartPos(e.type === 'mousedown' ? e.pageX : e.touches[0].clientX);
  };

  const handleDragMove = (e) => {
    if (!isDragging) return;

    const currentPosition = e.type === 'mousemove' ? e.pageX : e.touches[0].clientX;
    const diff = currentPosition - startPos;

    if (Math.abs(diff) > 50) { // Minimum swipe distance
      if (diff > 0) {
        handlePrevious();
      } else {
        handleNext();
      }
      setIsDragging(false);
    }
  };

  const handleDragEnd = () => {
    setIsDragging(false);
  };


  return (
    <div className="w-full">
      <div
        className="bg-black grid place-items-center p-8 pt-20 relative"
        style={{
          backgroundImage: `url(${grid1})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
          height: "100%",
          width: "100%",
        }}
      >
        <button className=" rounded-[30px] py-[10px] sm:py-[16px] flex items-center hover:shadow-[0_0_7px_rgba(59,59,59,0.79)] transition-all duration-200">
          <div className="inner rounded-[30px]">
            <span className="relative font-[Inter] z-10 bg-[#3B3B3B] px-5 sm:px-5 py-[12px] sm:py-[18px] rounded-[30px] text-md text-white">
              What our creators have to say
            </span>
          </div>
        </button>
        <div className="relative min-h-[400px] md:min-h-[300px] lg:min-h-[200px] w-full py-16">
          {/* Background Image Container */}

          <div
            className="absolute inset-0 bg-center bg-contain opacity-50"

          />

          <div className="absolute inset-0 bg-black/40" />

          <div className="relative h-full w-full max-w-6xl mx-auto px-4 md:px-6 lg:px-8 flex flex-col justify-center items-center py-0 md:py-0">


            <div className="relative w-full max-w-3xl">
              <button
                onClick={handlePrevious}
                className="hidden md:block absolute left-0 top-1/2 -translate-y-1/2 -translate-x-2 md:-translate-x-4 lg:-translate-x-8 z-10 bg-black/50 hover:bg-black/75 text-white rounded-full p-1.5 md:p-2 transition-colors"
                aria-label="Previous testimonial"
              >
                <ChevronLeft size={20} className="w-4 h-4 md:w-6 md:h-6" />
              </button>
              <button
                onClick={handleNext}
                className="hidden md:block absolute right-0 top-1/2 -translate-y-1/2 translate-x-2 md:translate-x-4 lg:translate-x-8 z-10 bg-black/50 hover:bg-black/75 text-white rounded-full p-1.5 md:p-2 transition-colors"
                aria-label="Next testimonial"
              >
                <ChevronRight size={20} className="w-4 h-4 md:w-6 md:h-6" />
              </button>

              <div
                ref={slideContainerRef}
                className="bg-[#121212] backdrop-filter backdrop-blur-SM bg-opacity-90 bg-noise 
        rounded-2xl md:rounded-[30px] p-4 sm:p-6 md:p-8 lg:p-10 mx-auto shadow-lg 
        w-full sm:w-[80%] md:w-[70%] lg:w-[60%] select-none"
                onMouseDown={handleDragStart}
                onMouseMove={handleDragMove}
                onMouseUp={handleDragEnd}
                onMouseLeave={handleDragEnd}
                onTouchStart={handleDragStart}
                onTouchMove={handleDragMove}
                onTouchEnd={handleDragEnd}
                style={{
                  cursor: isDragging ? 'grabbing' : 'grab',
                  transition: 'transform 0.3s ease-out'
                }}
              >
                <div className="flex flex-col sm:flex-row items-start gap-4 md:gap-6">
                  <div className="w-12 h-12 md:w-16 md:h-16 rounded-full overflow-hidden flex-shrink-0">
                    <img
                      src={testimonials[currentIndex].image}
                      alt={testimonials[currentIndex].name}
                      className="w-full h-full object-cover"
                      draggable="false"
                    />
                  </div>

                  <div className="flex-1 space-y-2 md:space-y-3">
                    <div className="space-y-0.5 md:space-y-1">
                      <h3 className="text-xl font-[Amenti] md:text-2xl font-light text-white">
                        {testimonials[currentIndex].name}
                      </h3>
                      <p className="text-gray-500 font-[Inter] text-xs md:text-sm">
                        {testimonials[currentIndex].role}
                      </p>
                    </div>
                    <p className="text-gray-400 font-[Inter] text-sm md:text-base leading-relaxed">
                      {testimonials[currentIndex].testimonial}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex justify-center items-center gap-2 md:gap-3 mt-4 md:mt-8">
                {testimonials.map((_, index) => (
                  <div
                    key={index}
                    className={`h-[2px] rounded-full transition-all duration-300 ${index === currentIndex ? 'w-8 md:w-12 bg-white' : 'w-4 md:w-6 bg-gray-600'
                      }`}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="w-full font-[Amenti] px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <h1 className="bg-gradient-text py-4 sm:py-6 md:py-10 lg:py-20 text-lg sm:text-xl md:text-2xl lg:text-4xl mb-4 sm:mb-6 md:mb-8 lg:mb-12 text-left font-Amenti sm:ml-0 lg:ml-16">
          At Velocity — We craft AI-driven prompts <br className="hidden sm:block" /> that engage your audience
          with clarity <br className="hidden sm:block" /> and creativity.
        </h1>
      </div>


      {/* Backward scrolling section */}
      <div className="inner1 overflow-hidden px-4">
        <div className="wrapper row1 flex">
          <section
            className="flex animate-scroll"
            style={{ "--speed": `${speed}ms` }}
          >
            {images.map(({ id, image }) => (
              <div className="image flex-shrink-0" key={id}>
                <img
                  src={image}
                  alt={id}
                  className="w-[200px] sm:w-[300px] md:w-[350px] lg:w-[421px]
                      h-[200px] sm:h-[300px] md:h-[350px] lg:h-[421px]
                      object-cover rounded-[20px] sm:rounded-[30px] md:rounded-[40px]
                      mr-3 sm:mr-4 md:mr-6"
                />
              </div>
            ))}
            {/* Duplicate images for seamless loop */}
            {images.map(({ id, image }) => (
              <div className="image flex-shrink-0" key={`duplicate-${id}`}>
                <img
                  src={image}
                  alt={id}
                  className="w-[200px] sm:w-[300px] md:w-[350px] lg:w-[421px]
                      h-[200px] sm:h-[300px] md:h-[350px] lg:h-[421px]
                      object-cover rounded-[20px] sm:rounded-[30px] md:rounded-[40px]
                      mr-3 sm:mr-4 md:mr-6"
                />
              </div>
            ))}
          </section>
        </div>
      </div>

      {/* Forward scrolling section */}
      <div className="inner1 overflow-hidden px-4 mt-2 sm:mt-4 relative">
        {/* Gradient overlays */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: `
      linear-gradient(180deg, rgba(0, 98, 153, 0.3) 0%, #005F91 100%), 
      linear-gradient(180deg, rgba(0, 98, 153, 0.3) 77%, #4AAFE0 111.61%)
    `,
            zIndex: 10,
            mixBlendMode: 'overlay',
          }}
        />
        <div className="wrapper row2 flex relative">
          <section
            className="flex animate-scroll-reverse"
            style={{ "--speed": `${speed}ms` }}
          >
            {images.map(({ id, image }) => (
              <div className="image flex-shrink-0" key={id}>
                <img
                  src={image}
                  alt={id}
                  className="w-[200px] sm:w-[300px] md:w-[350px] lg:w-[421px]
                  h-[200px] sm:h-[300px] md:h-[350px] lg:h-[421px]
                  object-cover rounded-[20px] sm:rounded-[30px] md:rounded-[40px]
                  mr-3 sm:mr-4 md:mr-6"
                />
              </div>
            ))}
            {/* Duplicate images for seamless loop */}
            {images.map(({ id, image }) => (
              <div className="image flex-shrink-0" key={`duplicate-${id}`}>
                <img
                  src={image}
                  alt={id}
                  className="w-[200px] sm:w-[300px] md:w-[350px] lg:w-[421px]
                  h-[200px] sm:h-[300px] md:h-[350px] lg:h-[421px]
                  object-cover rounded-[20px] sm:rounded-[30px] md:rounded-[40px]
                  mr-3 sm:mr-4 md:mr-6"
                />
              </div>
            ))}
          </section>
        </div>

        {/* Bottom fade gradient for smoother transition */}
        <div
          className="absolute bottom-0 left-0 right-0 h-24 sm:h-28 md:h-32 lg:h-36 xl:h-40 pointer-events-none gradient-bottom"
          style={{
            background: 'linear-gradient(to bottom, transparent, rgba(0, 138, 203, 0.3))',
          }}
        />

      </div>
    </div>
  );
};

export default Carousel;