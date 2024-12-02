import React, { useState } from 'react';
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
import girl from "../assets/girl_img.png"; // Import the girl image

const Carousel = ({ speed = 30000 }) => {
  const [currentSlide, setCurrentSlide] = useState(0);

  const images = [
    img1, img2, img3, img4, img5, img6, img7, img8, img9, img10, img11, img12
  ].map((image) => ({
    id: crypto.randomUUID(),
    image
  }));

  const testimonials = [
    {
      name: "Shrishti Munjal",
      role: "CEO Zetoupe",
      quote: "Velocity feels like having a creative partner who just gets you. It takes the guesswork out of crafting prompts, saving me hours and delivering spot-on results. Intuitive, smooth, and a total game-changer for anyone working with AI!",
      image: girl // Use the girl image here
    }
  ];

  return (
    <>
      {/* Testimonial Section */}
      <div
        className="bg-black grid place-items-center p-8 relative"
        style={{ backgroundImage: `url(${grid1})`, backgroundSize: 'cover', backgroundPosition: 'center' }}
      >
        {/* Grid background */}
        <div className="absolute inset-0 grid grid-cols-12 grid-rows-12 gap-4 opacity-10">
          {Array.from({ length: 144 }).map((_, i) => (
            <div key={i} className="border border-gray-700" />
          ))}
        </div>
        <div className="relative w-full max-w-4xl">
          <div className="flex justify-center mb-12">
            <div
              className="rounded-full px-6 py-2"
              style={{ backgroundColor: '#0B0B0B' }} // Set the background color to #0B0B0B
            >
              <h2 className="text-gray-300">What our creators say</h2>
            </div>

          </div>
          <div className="bg-[#0B0B0B] rounded-3xl p-8 relative w-[647px] mx-auto">
  <div className="flex items-start gap-6">
    <img
      src={testimonials[currentSlide].image} // Use the girl image here
      alt="Profile"
      className="w-16 h-16 rounded-full object-cover"
    />
    <div className="space-y-4">
      <div>
        <h3 className="text-2xl font-light text-white mb-1">
          {testimonials[currentSlide].name}
        </h3>
        <p className="text-gray-400">
          {testimonials[currentSlide].role}
        </p>
      </div>
      <p className="text-gray-300 leading-relaxed">
        {testimonials[currentSlide].quote}
      </p>
    </div>
  </div>
</div>


          <div className="flex justify-center gap-2 mt-8">
            {testimonials.map((_, index) => (
              <button
                key={index}
                className={`w-8 h-1 rounded-full transition-colors ${index === currentSlide ? 'bg-white' : 'bg-gray-600'}`}
                onClick={() => setCurrentSlide(index)}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Main Heading Section */}
      <div className="sm:w-[70%] w-full">
        <h1 className="bg-gradient-text pt-20 sm:pt-40 text-3xl sm:text-4xl mb-12 w-[90%] sm:w-[60%] mx-auto font-[Amenti]">
          At Velocity — We craft AI driven prompts that engage your audience with clarity and creativity.
        </h1>
      </div>

      {/* Backward scrolling section */}
      <div className="inner1 overflow-hidden">
        <div className="wrapper row1">
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
        </div>
      </div>

      {/* Forward scrolling section */}
      <div className="inner1 overflow-hidden">
        <div className="wrapper row2">
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
          <section style={{ "--speed": `${speed}ms` }}>
            {images.map(({ id, image }) => (
              <div className="image" key={id}>
                <img src={image} alt={id} />
              </div>
            ))}
          </section>
        </div>
      </div>
    </>
  );
};

export default Carousel;
