import React, { useState, useEffect } from "react";
import { Menu } from "lucide-react";

const ScrollAnchor = ({ scrollRefs }) => {
  const [selected, setSelected] = useState(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navigationItems = [
    {
      id: 2,
      label: "How it works",
      refKey: "howItWorks",
    },
    {
      id: 3,
      label: "Built for",
      refKey: "built",
    },
    {
      id: 4,
      label: "Reviews",
      refKey: "carousel",
    },
  ];

  const handleScroll = () => {
    for (const item of navigationItems) {
      const targetRef = scrollRefs[item.refKey];
      if (targetRef?.current) {
        const rect = targetRef.current.getBoundingClientRect();
        const sectionCenter = rect.top + rect.height / 3;
        if (sectionCenter >= 0 && sectionCenter <= window.innerHeight) {
          setSelected(item.id);
          break;
        }
      }
    }
  };

  useEffect(() => {
    window.addEventListener("scroll", handleScroll);
    return () => {
      window.removeEventListener("scroll", handleScroll);
    };
  }, [scrollRefs]);

  const handleClick = (id, refKey) => {
    setSelected(id);
    setIsMobileMenuOpen(false);
    const targetRef = scrollRefs[refKey];
    if (targetRef?.current) {
      const navbarHeight = window.innerWidth < 640 ? 70 : 100;
      const elementPosition = targetRef.current.getBoundingClientRect().top + window.pageYOffset;
      const offsetPosition = elementPosition - navbarHeight;

      window.scrollTo({
        top: offsetPosition,
        behavior: "smooth",
      });
    }
  };

  return (
    <>
      {/* Mobile Menu Button */}
      <div className="sm:hidden">
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2 rounded-full bg-black/30 backdrop-blur-sm border border-[#1E1E1E]"
        >
          <Menu className="w-6 h-6 text-gray-400" />
        </button>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="absolute top-16 left-4 right-4 bg-black/90 backdrop-blur-md border border-[#1E1E1E] rounded-xl p-2 sm:hidden z-50">
          <div className="flex flex-col space-y-2">
            {navigationItems.map((item) => (
              <button
                key={item.id}
                className={`flex items-center transition-all duration-300 text-base px-4 py-2 rounded-lg w-full ${
                  selected === item.id ? "text-white bg-[#00141D]" : "text-gray-400"
                }`}
                onClick={() => handleClick(item.id, item.refKey)}
              >
                <span
                  className={`w-2 h-2 rounded-full mr-2 ${
                    selected === item.id ? "bg-[#008ACB]" : "bg-gray-500"
                  }`}
                />
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Tablet/Desktop Menu */}
      <div className="hidden sm:flex justify-center items-center bg-black/30 backdrop-blur-sm border border-[#1E1E1E] rounded-full w-fit sm:ml-4 md:ml-8 lg:ml-12">
        <div className="flex items-center px-2 py-2 md:px-4 md:py-3 space-x-2 md:space-x-4 lg:space-x-7">
          {navigationItems.map((item) => (
            <button
              key={item.id}
              className={`flex items-center transition-all duration-300 text-sm md:text-base lg:text-lg px-3 py-1 rounded-3xl ${
                selected === item.id ? "text-white bg-[#00141D]" : "text-gray-400"
              }`}
              onClick={() => handleClick(item.id, item.refKey)}
            >
              <span
                className={`w-2 h-2 rounded-full mr-2 ${
                  selected === item.id ? "bg-[#008ACB]" : "bg-gray-500"
                }`}
              />
              {item.label}
            </button>
          ))}
        </div>
      </div>
    </>
  );
};

export default ScrollAnchor;