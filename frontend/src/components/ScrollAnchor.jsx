import React, { useState, useEffect } from "react";

const ScrollAnchor = ({ scrollRefs }) => {
  const [selected, setSelected] = useState(null);

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

  // Function to check which section is currently in view
  const handleScroll = () => {
    for (const item of navigationItems) {
      const targetRef = scrollRefs[item.refKey];
      if (targetRef?.current) {
        const rect = targetRef.current.getBoundingClientRect();
        // Check if the center of the section is in the viewport
        const sectionCenter = rect.top + rect.height / 3;
        if (sectionCenter >= 0 && sectionCenter <= window.innerHeight) {
          setSelected(item.id); // Set the selected section based on scroll position
          break;
        }
      }
    }
  };

  useEffect(() => {
    // Attach the scroll event listener
    window.addEventListener("scroll", handleScroll);

    // Cleanup the event listener on component unmount
    return () => {
      window.removeEventListener("scroll", handleScroll);
    };
  }, [scrollRefs]); // Re-run effect if scrollRefs change

  const handleClick = (id, refKey) => {
    setSelected(id); // Update selection immediately on click
    const targetRef = scrollRefs[refKey];
    if (targetRef?.current) {
      // Add offset for fixed navbar
      const navbarHeight = 100; // Adjust this value based on your navbar height
      const elementPosition = targetRef.current.getBoundingClientRect().top + window.pageYOffset; // Get the position relative to the document
      const offsetPosition = elementPosition - navbarHeight;

      // Scroll to the target position with smooth behavior
      window.scrollTo({
        top: offsetPosition,
        behavior: "smooth",
      });
    }
  };

  return (
    <div className="justify-center items-center sm:space-x-0 lg:space-x-7 bg-black/30 backdrop-blur-sm border border-[#1E1E1E] px-4 py-3 rounded-full w-fit mx-auto hidden sm:flex">
      {navigationItems.map((item) => (
        <button
          key={item.id}
          className={`flex items-center transition-all duration-300 text-lg px-3 py-1 rounded-3xl ${
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
  );
};

export default ScrollAnchor;
