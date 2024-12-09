import React from 'react';

const BuiltFor = () => {
  const categories = [
    {
      img: "https://toteminteractive.in/velosty/built1.png",
      title: "Designers & Artists",
      description: "Bring your creative visions to life with prompts tailored for visual storytelling, concept art, and beyond.",
    },
    {
      img: "https://toteminteractive.in/velosty/built2.png",
      title: "Marketers & Copywriters",
      description: "Craft compelling content with ease—whether it's ad copy, brand messaging, or social media posts.",
    },
    {
      img: "https://toteminteractive.in/velosty/built3.png",
      title: "Students & Educators",
      description: "Simplify research, generate ideas, or prepare lesson plans with precision and creativity.",
    },
    {
      img: "https://toteminteractive.in/velosty/built4.png",
      title: "Professionals & Teams",
      description: "Streamline your workflow with professional-grade prompts optimized for business use.",
    },
    {
      img: "https://toteminteractive.in/velosty/built5.png",
      title: "Hobbyists & Enthusiasts",
      description: "Explore endless possibilities and make your creative projects stand out with minimal effort.",
    }
  ];

  return (
    <div className="w-full" style={{ backgroundColor: '#000000' }}>
      <div className="max-w-7xl mx-auto py-6">
        <h2 className="font-[Amenti] text-4xl text-center mb-12 mt-8 text-white">Built For</h2>
        
        <div className="flex flex-col gap-20 pb-12">
          {/* First row - 3 items */}
          <div className="flex flex-wrap justify-center gap-20 md:gap-6 sm:gap-4">
            {categories.slice(0, 3).map((category, index) => (
              <div 
                key={index}
                className="flex flex-col items-center text-center max-w-sm w-full sm:w-1/2 md:w-1/3"
              >
                <div className="w-40 h-40 bg-gray-900 rounded-lg mb-6 flex items-center justify-center overflow-hidden">
                  <img
                    src={category.img}
                    alt={category.title}
                    className="w-full h-full object-cover"
                  />
                </div>
                
                <h3 className="text-white text-xl font-medium mb-3">
                  {category.title}
                </h3>
                
                <p className="text-gray-400 text-xs w-2/3 sm:w-full">
                  {category.description}
                </p>
              </div>
            ))}
          </div>

          {/* Second row - 2 items */}
          <div className="flex flex-wrap justify-center gap-8 sm:gap-4">
            {categories.slice(3).map((category, index) => (
              <div 
                key={index + 3}
                className="flex flex-col items-center text-center max-w-sm w-full sm:w-1/2"
              >
                <div className="w-40 h-40 bg-gray-900 rounded-lg mb-6 flex items-center justify-center overflow-hidden">
                  <img
                    src={category.img}
                    alt={category.title}
                    className="w-full h-full object-cover"
                  />
                </div>
                
                <h3 className="text-white text-xl font-medium mb-3">
                  {category.title}
                </h3>
                
                <p className="text-gray-400 text-xs w-2/3 sm:w-full">
                  {category.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BuiltFor;
