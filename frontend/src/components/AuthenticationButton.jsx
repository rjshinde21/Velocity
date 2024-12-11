import React from 'react';
import { Link } from 'react-router-dom';
import { UserRound } from 'lucide-react';

const AuthButton = ({ variant = 'navbar' }) => {
  const isLoggedIn = false; // Replace this with your actual auth state management

  const navbarButtonStyles = "navbtn rounded-[30px] bg-[#0a0a0a] py-[10px] sm:py-[16px] flex items-center hover:shadow-[0_0_7px_rgba(255,255,255,0.7)] transition-all duration-200";
  const footerButtonStyles = "bg-black text-white px-4 sm:px-6 py-3 sm:py-4 rounded-full border border-gray-700 hover:bg-gray-900 transition-colors whitespace-nowrap";

  const userIconStyles = "border rounded-full w-8 h-8 sm:w-10 sm:h-10";

  if (!isLoggedIn) {
    return (
      <Link to="/register">
        {variant === 'navbar' ? (
          <button className={navbarButtonStyles}>
            <div className="inner rounded-[30px]">
              <span className="relative z-10 bg-black px-5 sm:px-9 py-[12px] sm:py-[18px] rounded-[30px] text-lg text-white">
                Get Started
              </span>
            </div>
          </button>
        ) : (
          <button className={footerButtonStyles}>
            Get Started
          </button>
        )}
      </Link>
    );
  }

  return (
    <Link to="/profile">
      <UserRound className={userIconStyles} />
    </Link>
  );
};

export default AuthButton;