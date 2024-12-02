import React, { useState, useEffect } from "react";

const BuyCredits = () => {
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
  };

  return (
    <div className="min-h-screen bg-black text-white p-8 flex flex-col items-center">
      {/* Logo */}
      <div className="flex items-center gap-2 mb-16">
        <span className="text-2xl">✓</span>
        <span className="text-2xl">Velocity</span>
      </div>

      {/* Main Content */}
      <div className="w-full max-w-2xl">
        <h1 className="text-2xl mb-8 text-center">Buy Credits</h1>

        {/* Credit Options Grid */}
        <div className="grid grid-cols-3 gap-4 mb-12">
          {creditOptions.map(({ amount, credits }) => (
            <button
              key={amount}
              onClick={() => handleAmountSelect(amount, credits)}
              className={`
                py-4 px-6 rounded-xl text-xl
                ${selectedAmount === amount 
                  ? 'bg-gray-700 border-2 border-blue-500' 
                  : 'bg-gray-800 hover:bg-gray-700'}
                transition-all duration-200
              `}
            >
              ${amount}
            </button>
          ))}
        </div>

        {/* Credits Display */}
        <div className="text-center mb-8">
          <h2 className="text-gray-400 mb-4">Credits you will get</h2>
          <div className="inline-block bg-gray-800 rounded-xl px-8 py-3">
            {credits} Credits
          </div>
        </div>

        {/* Next Button */}
        <button 
          className="w-full max-w-xs mx-auto block py-3 px-8 rounded-full bg-black border border-blue-500 hover:bg-gray-900 transition-colors duration-200 relative group"
          style={{
            boxShadow: '0 0 20px rgba(59, 130, 246, 0.5)'
          }}
        >
          <span className="relative z-10">Next</span>
          <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-600 to-blue-400 opacity-0 group-hover:opacity-10 transition-opacity duration-200"></div>
        </button>
      </div>
    </div>
  );
};

export default BuyCredits;