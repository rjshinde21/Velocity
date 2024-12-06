import React, { useState, useRef } from "react";
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
import grid1 from "../assets/grid.png";
import girl from "../assets/girl_img.png";
import noise from "../assets/noise.png";

const Carousel = ({ speed = 30000 }) => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [startPosition, setStartPosition] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const slideContainerRef = useRef(null);

  const images = [
    img1,
    img2,
    img3,
    img4,
    img5,
    img6,
    img7,
    img8,
    img9,
    img10,
    img11,
    img12,
  ].map((image) => ({
    id: crypto.randomUUID(),
    image,
  }));

  const testimonials = [
    {
      name: "Shrishti Munjal",
      role: "CEO Zetoupe",
      quote:
        "Velocity feels like having a creative partner who just gets you. It takes the guesswork out of crafting prompts, saving me hours and delivering spot-on results. Intuitive, smooth, and a total game-changer for anyone working with AI!",
      image: girl,
    },
    {
      name: "Aditi Pathak",
      role: "CEO Swiggy",
      quote: "creative partner who just gets you. It takes the guesswork out of crafting prompts, saving me hours and delivering spot-on results. Intuitive, smooth, and a total game-changer for anyone working with AI!",
      image: girl,
    },
    {
      name: "Shruti Shelar",
      role: "Employe",
      quote: "It takes the guesswork out of crafting prompts, saving me hours and delivering spot-on results. Intuitive, smooth, and a total game-changer for anyone working with AI! creative partner who just gets you",
      image: girl,
    },
  ];

  const handleDragStart = (e) => {
    setIsDragging(true);
    setStartPosition(e.type === 'mousedown' ? e.pageX : e.touches[0].pageX);
  };

  const handleDragMove = (e) => {
    if (!isDragging) return;

    const currentPosition = e.type === 'mousemove' ? e.pageX : e.touches[0].pageX;
    const difference = startPosition - currentPosition;

    if (Math.abs(difference) > 50) { // Minimum drag distance
      if (difference > 0 && currentSlide < testimonials.length - 1) {
        setCurrentSlide(prev => prev + 1);
      } else if (difference < 0 && currentSlide > 0) {
        setCurrentSlide(prev => prev - 1);
      }
      setIsDragging(false);
    }
  };

  const handleDragEnd = () => {
    setIsDragging(false);
  };

  return (
    <>
      {/* Testimonial Section */}
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
        {/* Grid background */}
        <div className="absolute inset-0 grid grid-cols-12 grid-rows-12 gap-4 opacity-10">
          {Array.from({ length: 144 }).map((_, i) => (
            <div key={i} className="border border-gray-700" />
          ))}
        </div>

        <div className="relative w-full max-w-4xl">
          <div className="flex justify-center mb-8">
            <div
              className="rounded-full px-6 py-2"
              style={{ backgroundColor: "#0B0B0B" }}
            >
              <h2 className="text-gray-300 text-center text-sm sm:text-lg">
                What our creators say
              </h2>
            </div>
          </div>

          {/* Main Content Area */}
          <div className="relative flex items-center">
            {/* Left Arrow */}
            <button
              onClick={() => setCurrentSlide((prev) => (prev === 0 ? testimonials.length - 1 : prev - 1))}
              className="absolute left-0 sm:-left-10 text-gray-700 text-3xl sm:text-4xl p-0"
            >
              &lt;
            </button>

            <div
              ref={slideContainerRef}
              className="flex gap-6 w-full justify-center"
              onMouseDown={handleDragStart}
              onMouseMove={handleDragMove}
              onMouseUp={handleDragEnd}
              onMouseLeave={handleDragEnd}
              onTouchStart={handleDragStart}
              onTouchMove={handleDragMove}
              onTouchEnd={handleDragEnd}
              style={{
                cursor: isDragging ? "grabbing" : "grab",
                userSelect: "none",
              }}
            >
              <div
                className="bg-[#0B0B0B] rounded-3xl p-6 sm:p-8 relative w-full max-w-lg transition-transform duration-300"
                style={{
                  backgroundImage: `url(${noise})`, // Set the noise image as the background
                  backgroundSize: "cover", // Ensures the image covers the whole div
                  backgroundPosition: "center", // Centers the background image
                }}
              >
                <div className="flex items-start gap-4 sm:gap-6">
                  <img
                    src={testimonials[currentSlide].image}
                    alt="Profile"
                    className="w-14 h-14 sm:w-16 sm:h-16 rounded-full object-cover"
                    draggable="false"
                  />
                  <div className="space-y-3">
                    <div>
                      <h3 className="text-lg sm:text-2xl font-light text-white mb-2">
                        {testimonials[currentSlide].name}
                      </h3>
                      <p className="text-gray-400 text-sm sm:text-base">
                        {testimonials[currentSlide].role}
                      </p>
                    </div>
                    <p className="text-gray-300 leading-relaxed text-sm sm:text-base">
                      {testimonials[currentSlide].quote}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Arrow */}
            <button
              onClick={() => setCurrentSlide((prev) => (prev === testimonials.length - 1 ? 0 : prev + 1))}
              className="absolute right-0 sm:-right-8 text-gray-700 text-3xl sm:text-4xl p-0"
            >
              &gt;
            </button>
          </div>

          {/* Dots for navigation */}
          <div className="flex justify-center gap-2 mt-6">
            {testimonials.map((_, index) => (
              <button
                key={index}
                className={`w-6 h-1 sm:w-8 transition-colors rounded-full ${index === currentSlide ? "bg-white" : "bg-gray-600"
                  }`}
                onClick={() => setCurrentSlide(index)}
              />
            ))}
          </div>
        </div>
      </div>


      {/* Main Heading Section */}
      <div className="w-full px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <h1 className="bg-gradient-text py-6 sm:py-10 lg:py-20 text-xl sm:text-2xl lg:text-4xl mb-6 sm:mb-8 lg:mb-12 text-left font-[Amenti] sm:ml-0 lg:ml-16">
          At Velocity — We craft AI-driven prompts <br /> that engage your audience
          with clarity <br /> and creativity.
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
    </>
  );
};

export default Carousel;
