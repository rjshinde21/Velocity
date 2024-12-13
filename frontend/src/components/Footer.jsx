import React from 'react';
import { Link } from 'react-router-dom';
import { Instagram, Linkedin, UserRound } from 'lucide-react';

const Footer = ({ isLoggedIn }) => {
  return (
    <footer className="bg-black text-gray-400 py-20 sm:py-8 md:py-12 lg:py-16">
      <div className="container mx-auto px-4 sm:px-6 lg:px-28">
        <div className="max-w-7xl mx-0">
          {/* Main content */}
          <div className="flex flex-col sm:flex-row justify-between items-start gap-6 sm:gap-8 mb-8 sm:mb-12">
            {/* Text content */}
            <div className="flex flex-col gap-3 sm:gap-4 items-start w-full sm:w-2/3">
              <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold leading-tight font-[Inter]">
                GENERATE SMARTER<br className="hidden sm:block" />
                <span className="block sm:inline"> PROMPTS. FASTER.</span>
              </h1>
              <p className="text-sm sm:text-base text-gray-700 leading-relaxed max-w-md font-[Inter]">
                Transform your ideas with precision and creativity
              </p>
            </div>

            {/* CTA Button */}
            <a
              href="https://chromewebstore.google.com/category/extensions?hl=en-US&utm_source=ext_sidebar"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full sm:w-auto"
            >
              <button className="navbtn rounded-[30px] bg-[#0a0a0a] py-[10px] sm:py-[16px] flex items-center hover:shadow-[0_0_7px_rgba(255,255,255,0.7)] transition-all duration-200">
                <div className="inner rounded-[30px]">
                  <span className="relative z-10 bg-black px-5 sm:px-9 py-[12px] sm:py-[18px] rounded-[30px] text-lg text-white whitespace-nowrap">
                    Get Started
                  </span>
                </div>
              </button>
            </a>
          </div>

          {/* Designer credit and logo section */}
          <div className="mt-10 sm:mt-12 lg:mt-16">
            {/* Designer credit */}
            <a
              href="https://www.toteminteractive.in/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs sm:text-sm sm:text-left mb-0 sm:mb-0 font-[Urbanist] hover:text-blue-500"
            >
              Designed by TOTEM INTERACTIVE
            </a>


            {/* Logo and social icons container */}
            <div className="relative">
              {/* VELOCITY Text */}
              <div className="font-[Amenti] text-[2.5rem] sm:text-[4rem] md:text-[6rem] lg:text-[8rem] xl:text-[10rem]
                font-bold tracking-wider leading-none
                 sm:text-left
                transform transition-transform duration-300">
                VELOCITY
              </div>

              {/* Social Icons */}
              <div className="flex gap-3 sm:gap-4
                absolute bottom-1 right-0
                sm:bottom-2 md:bottom-4 lg:bottom-6 mr-10">
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