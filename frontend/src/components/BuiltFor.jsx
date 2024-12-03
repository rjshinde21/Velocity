import React from 'react';

const BuiltFor = () => {
  const categories = [
    {
        img:"https://toteminteractive.in/velosty/built1.png",
      title: "Designers & Artists",
      description: "Bring your creative visions to life with prompts tailored for visual storytelling, concept art, and beyond.",
    },
    {
        img:"https://toteminteractive.in/velosty/built2.png",
      title: "Marketers & Copywriters",
      description: "Craft compelling content with ease—whether it's ad copy, brand messaging, or social media posts.",
    },
    {
        img:"https://toteminteractive.in/velosty/built3.png",
      title: "Students & Educators",
      description: "Simplify research, generate ideas, or prepare lesson plans with precision and creativity.",
    },
    {
        img:"https://toteminteractive.in/velosty/built4.png",
      title: "Professionals & Teams",
      description: "Streamline your workflow with professional-grade prompts optimized for business use.",
    },
    {
        img:"https://toteminteractive.in/velosty/built5.png",
      title: "Hobbyists & Enthusiasts",
      description: "Explore endless possibilities and make your creative projects stand out with minimal effort.",
    }
  ];

  return (
  <div className="w-full" style={{ backgroundColor: '#090909' }}>
  <div className="max-w-7xl mx-auto py-6">
    <h2 className="text-4xl text-center mb-16 text-white">Built For</h2>
    
    <div className="flex flex-col gap-12 pb-6">
      {/* First row - 3 items */}
      <div className="flex flex-col md:flex-row gap-8 justify-center">
        {categories.slice(0, 3).map((category, index) => (
          <div 
            key={index}
            className="flex flex-col items-center text-center max-w-sm"
          >
            <div className="w-28 h-28 bg-gray-900 rounded-lg mb-6 flex items-center justify-center overflow-hidden">
              <img
                src={category.img}
                alt={category.title}
                className="w-full h-full object-cover"
              />
            </div>
            
            <h3 className="text-white text-xl font-medium mb-3">
              {category.title}
            </h3>
            
            <p className="text-gray-400 text-xs w-2/3">
              {category.description}
            </p>
          </div>
        ))}
      </div>

      {/* Second row - 2 items */}
      <div className="flex flex-col md:flex-row gap-8 justify-center">
        {categories.slice(3).map((category, index) => (
          <div 
            key={index + 3}
            className="flex flex-col items-center text-center max-w-sm"
          >
            <div className="w-28 h-28 bg-gray-900 rounded-lg mb-6 flex items-center justify-center overflow-hidden">
              <img
                src={category.img}
                alt={category.title}
                className="w-full h-full object-cover"
              />
            </div>
            
            <h3 className="text-white text-xl font-medium mb-3">
              {category.title}
            </h3>
            
            <p className="text-gray-400 text-sm">
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