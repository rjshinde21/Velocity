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
    <div className="w-full font-[Inter]" style={{ backgroundColor: '#000000' }}>
      <style>
        {`
          /* Tablet-specific styles */
          @media screen and (min-width: 712px) and (max-width: 853px) {
            .built-for-container {
              padding: 3rem 1.5rem !important;
            }
            
            .built-for-title {
              font-size: 2.5rem !important;
              margin-bottom: 2.5rem !important;
              margin-top: 1.5rem !important;
            }
            
            .category-grid {
              gap: 2rem !important;
            }
            
            .category-item {
              max-width: 300px !important;
              padding: 0 1rem !important;
            }
            
            .image-container {
              width: 120px !important;
              height: 120px !important;
              margin-bottom: 1.25rem !important;
            }
            
            .category-title {
              font-size: 1.125rem !important;
              margin-bottom: 0.75rem !important;
            }
            
            .category-description {
              font-size: 0.875rem !important;
              width: 85% !important;
              margin: 0 auto !important;
              line-height: 1.4 !important;
            }

            .second-row {
              // margin-top: 2.5rem !important;
              gap: 2.5rem !important;
            }
          }

          /* Larger tablet-specific styles */
          @media screen and (min-width: 853px) and (max-width: 1280px) {
            .built-for-container {
              padding: 3rem 1.5rem !important;
            }
            
            .category-grid {
              gap: 2rem !important;
            }
            
            .category-item {
              max-width: 320px !important;
            }
            
            .image-container {
              width: 130px !important;
              height: 130px !important;
            }
            
            .category-description {
              width: 80% !important;
              font-size: 0.875rem !important;
            }

            .second-row {
              // margin-top: 3rem !important;
            }
          }
        `}
      </style>

      <div className="max-w-8xl mx-auto py-20 built-for-container">
        <h2 className="font-[Amenti] text-4xl text-center mb-12 mt-8 text-white built-for-title">
          Built For
        </h2>

        <div className="flex flex-col gap-16 lg:gap-20 pb-0">
          {/* First row - 3 items */}
          <div className="flex flex-wrap justify-center gap-12 sm:gap-8 md:gap-6">
            {categories.slice(0, 3).map((category, index) => (
              <div
                key={index}
                className={`flex flex-col items-center text-center w-full sm:w-[45%] md:w-[30%] max-w-sm min-w-[280px] transition-all duration-300 ${index === 2 ? 'hidden lg:flex' : ''
                  }`}
              >
                <div
                  className="w-32 h-32 sm:w-36 sm:h-36 lg:w-40 lg:h-40 bg-gray-900 rounded-lg mb-4 sm:mb-6 flex items-center justify-center overflow-hidden image-container"
                >
                  <img
                    src={category.img}
                    alt={category.title}
                    className="w-full h-full object-cover"
                  />
                </div>
                <h3 className="text-white text-lg sm:text-xl lg:text-2xl font-medium mb-2 sm:mb-3 category-title">
                  {category.title}
                </h3>
                <p className="text-gray-400 text-xs sm:text-sm lg:text-base w-3/4 sm:w-full category-description">
                  {category.description}
                </p>
              </div>
            ))}
          </div>

          {/* Second row - 2 items */}
          <div className="flex flex-wrap justify-center gap-12 sm:gap-8 md:gap-6">
            {categories.slice(3).map((category, index) => (
              <div
                key={index + 3}
                className="flex flex-col items-center text-center w-full sm:w-[45%] md:w-[30%] max-w-sm min-w-[280px] transition-all duration-300"
              >
                <div
                  className="w-32 h-32 sm:w-36 sm:h-36 lg:w-40 lg:h-40 bg-gray-900 rounded-lg mb-4 sm:mb-6 flex items-center justify-center overflow-hidden image-container"
                >
                  <img
                    src={category.img}
                    alt={category.title}
                    className="w-full h-full object-cover"
                  />
                </div>
                <h3 className="text-white text-lg sm:text-xl lg:text-2xl font-medium mb-2 sm:mb-3 category-title">
                  {category.title}
                </h3>
                <p className="text-gray-400 text-xs sm:text-sm lg:text-base w-3/4 sm:w-full category-description">
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