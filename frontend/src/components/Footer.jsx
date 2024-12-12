import React from 'react';
import { Link } from 'react-router-dom';
import { Instagram, Linkedin, UserRound } from 'lucide-react';

const Footer = ({ isLoggedIn }) => {
  return (
    <footer className="bg-black text-gray-400 py-20 sm:py-8 md:py-12 lg:py-16">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-0">
          {/* Main content */}
          <div className="flex flex-col sm:flex-row justify-between items-start gap-6 sm:gap-8 mb-8 sm:mb-12">
            {/* Text content */}
            <div className="flex flex-col gap-3 sm:gap-4 items-start w-full sm:w-2/3">
              <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold leading-tight">
                GENERATE SMARTER<br className="hidden sm:block" />
                <span className="block sm:inline"> PROMPTS. FASTER.</span>
              </h1>
              <p className="text-sm sm:text-base text-gray-700 leading-relaxed max-w-md">
                Transform your ideas with precision and creativity
              </p>
            </div>

            {/* CTA Button */}
            <div className="w-full sm:w-auto flex justify-start sm:justify-end items-start">
              <a 
                href="https://chromewebstore.google.com/category/extensions?hl=en-US&utm_source=ext_sidebar" 
                target="_blank"
                rel="noopener noreferrer"
                className="w-full sm:w-auto"
              >
                <button className="w-full sm:w-auto bg-black text-white px-10 sm:px-8 py-3 sm:py-4 
                  rounded-full border border-gray-700 hover:bg-gray-900 transition-all duration-200
                  text-sm sm:text-base font-medium whitespace-nowrap
                  hover:shadow-lg hover:border-gray-600">
                  Get Started
                </button>
              </a>
            </div>
          </div>

          {/* Designer credit and logo section */}
          <div className="mt-10 sm:mt-12 lg:mt-16">
            {/* Designer credit */}
            <p className="text-xs sm:text-sm sm:text-left mb-0 sm:mb-0">
              Designed by TOTEM INTERACTIVE
            </p>

            {/* Logo and social icons container */}
            <div className="relative">
              {/* VELOCITY Text */}
              <div className="font-Amenti text-[2.5rem] sm:text-[4rem] md:text-[6rem] lg:text-[8rem] xl:text-[10rem]
                font-bold tracking-wider leading-none
                 sm:text-left
                transform transition-transform duration-300">
                VELOCITY
              </div>

              {/* Social Icons */}
              <div className="flex gap-3 sm:gap-4
                absolute bottom-1 right-0
                sm:bottom-2 md:bottom-4 lg:bottom-6">
                <a
                  href="https://www.instagram.com/totem.interactive?igsh=MXRscW14NDNwOGdtbA=="
                  className="hover:text-white transition-colors p-1.5 sm:p-2
                    hover:scale-110 transform duration-200"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Instagram className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7" />
                </a>
                <a
                  href="https://www.linkedin.com/company/totem-interactive/posts/?feedView=all"
                  className="hover:text-white transition-colors p-1.5 sm:p-2
                    hover:scale-110 transform duration-200"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Linkedin className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7" />
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;