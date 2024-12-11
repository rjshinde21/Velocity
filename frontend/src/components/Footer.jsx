import React from 'react';
import { Link } from 'react-router-dom';
import { Instagram, Linkedin, UserRound } from 'lucide-react';

const Footer = ({ isLoggedIn }) => {
  return (
    <footer className="bg-black text-gray-400 py-8 sm:py-12 md:py-16">
      <div className="container mx-auto px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          {/* Main content */}
          <div className="mb-8 sm:mb-12 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6">
            <div className="flex flex-col gap-4 items-start w-full sm:w-auto">
              <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold leading-tight">
                GENERATE SMARTER<br />
                PROMPTS. FASTER.
              </h1>
              <p className="text-sm sm:text-base text-gray-700 leading-relaxed max-w-md">
                Transform your ideas with precision and creativity
              </p>
            </div>
            {/* Conditional rendering based on isLoggedIn */}
            <div className="w-full sm:w-auto flex justify-start sm:justify-end">
              {!isLoggedIn ? (
                <Link to="/register">
                  <button className="bg-black text-white px-4 sm:px-6 py-3 sm:py-4 rounded-full border border-gray-700 hover:bg-gray-900 transition-colors whitespace-nowrap">
                    Get Started
                  </button>
                </Link>
              ) : (
                <Link to="/profile">
                  <UserRound className="border rounded-full w-8 h-8 sm:w-10 sm:h-10" />
                </Link>
              )}
            </div>
          </div>

          {/* Designer credit and logo section */}
          <div className="space-y-6 sm:space-y-0">
            <p className="text-xs sm:text-sm text-center sm:text-left">
              Designed by TOTEM INTERACTIVE
            </p>

            {/* Logo and social icons */}
            <div className="relative flex flex-col items-center sm:items-start justify-between gap-4 sm:py-12">
              {/* VELOCITY Text */}
              <div className="font-Amenti text-[1.5rem] sm:text-[2rem] md:text-[6rem] lg:text-[8rem] xl:text-[10rem] 
                            font-bold tracking-wider leading-none text-center sm:text-left
                            w-full transform transition-transform duration-300">
                VELOCITY
              </div>
              
              {/* Social Icons */}
              <div className="flex gap-2 sm:gap-3 lg:gap-4 
                            absolute bottom-8 sm:bottom-12 lg:bottom-16 
                            right-2 sm:right-4 lg:right-6">
                <a
                  href="https://www.instagram.com/totem.interactive?igsh=MXRscW14NDNwOGdtbA=="
                  className="hover:text-white transition-colors p-1 sm:p-1.5"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Instagram className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7" />
                </a>
                <a
                  href="https://www.linkedin.com/company/totem-interactive/posts/?feedView=all"
                  className="hover:text-white transition-colors p-1 sm:p-1.5"
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