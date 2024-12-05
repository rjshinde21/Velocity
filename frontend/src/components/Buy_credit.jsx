import React, { useState, useEffect } from "react";
import velocitylogo from '../assets/velocitylogo.png';

const BuyCredits = ({ isOpen, onClose, setTopUpAmount, handlePayment }) => {
  const [selectedAmount, setSelectedAmount] = useState(null);
  const [credits, setCredits] = useState(0);

  const creditOptions = [
    { amount: 5, credits: 100 },
    { amount: 10, credits: 200 },
    { amount: 15, credits: 300 },
    { amount: 20, credits: 400 },
    { amount: 25, credits: 500 },
    { amount: 30, credits: 600 }
  ];

  const handleAmountSelect = (amount, credits) => {
    setSelectedAmount(amount);
    setCredits(credits);
    setTopUpAmount(amount);
  };

  const handleNextClick = () => {
    if (selectedAmount) {
      handlePayment(selectedAmount);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-80 z-50 flex items-center justify-center">
      <div className="relative w-full max-w-lg mx-4 bg-black border border-gray-800 rounded-2xl p-8">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white"
        >
          ✕
        </button>

        {/* Logo */}
        <div className="flex items-center justify-center gap-2 mb-16">
          <span className="text-2xl">
            <img src={velocitylogo} className="h-6 sm:h-8" alt="Velocity Logo" />
          </span>
          <span className="text-2xl text-white font-normal font-[Inter]">Velocity</span>
        </div>


        {/* Main Content */}
        <div className="w-full max-w-lg">
          <h1 className="text-2xl mb-8 text-center text-white font-normal font-[Inter]">Buy Credits</h1>

          {/* Credit Options Grid */}
          <div className="grid grid-cols-3 gap-2 mb-12">
            {creditOptions.map(({ amount, credits }) => (
              <button
                key={amount}
                onClick={() => handleAmountSelect(amount, credits)}
                className={`
                  py-4 px-6 rounded-xl text-xl text-white 
                  ${selectedAmount === amount
                    ? 'bg-gray-700 border-2 border-blue-500'
                    : 'bg-gray-800 hover:bg-gray-700'}
                  transition-all duration-200
                `} style={{ backgroundColor: '#2B2b2b' }}
              >
                ${amount}
              </button>
            ))}
          </div>

          {/* Credits Display */}
          <div className="text-center mb-8">
            <h2 className="text-gray-400 mb-4 text-white font-normal font-[Inter]">Credits you will get</h2>
            <div className="inline-block bg-gray-800 rounded-xl px-6 py-5 text-white font-normal font-[Inter]" style={{ backgroundColor: '#2B2b2b' }}> 
              {credits} Credits
            </div>
          </div>

          {/* Next Button */}
          <button
            onClick={handleNextClick}  // Changed to handleNextClick
            className="w-auto mx-auto block py-5 px-12 rounded-full bg-black border border-blue-500 hover:bg-gray-900 transition-colors duration-200 relative group"
            style={{
              boxShadow: '0 0 20px rgba(59, 130, 246, 0.5)'
            }}
          >
            <span className="relative z-10 text-xl text-white font-semibold font-[Inter]">Next</span>
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-600 to-blue-400 opacity-0 group-hover:opacity-10 transition-opacity duration-200"></div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default BuyCredits;