import React, { useState } from "react";
import velocityLogo from '../assets/velocitylogo.png';

const BuyCredits = ({ isOpen, onClose, setTopUpAmount, handlePayment }) => {
  const [selectedAmount, setSelectedAmount] = useState(null);
  const [credits, setCredits] = useState(0);
  const [isOtherSelected, setIsOtherSelected] = useState(false);
  const [customAmount, setCustomAmount] = useState("");

  const creditOptions = [
    { amount: 7.48, credits: 100 },
    { amount: 37.4, credits: 500 },
    { amount: 74.8, credits: 1000 },
    { amount: 374, credits: 5000 },
    { amount: 748, credits: 10000 },
  ];

  const calculateCreditsPerRupee = () => {
    const referenceOption = creditOptions[0];
    return referenceOption.credits / referenceOption.amount;
  };

  const handleAmountSelect = (amount, credits) => {
    setIsOtherSelected(false);
    setSelectedAmount(amount);
    setCredits(credits);
    setTopUpAmount({ amount, credits });
  };

  const handleOtherSelect = () => {
    setIsOtherSelected(true);
    setSelectedAmount(null);
    setCredits(0);
    setCustomAmount("");
  };

  const handleCustomInputChange = (e) => {
    let value = e.target.value;

    // Ensure the value is not more than 10
    if (value > 10) {
      value = "10";
    }

    setCustomAmount(value);

    if (value) {
      const amount = parseFloat(value);
      if (!isNaN(amount)) {
        const creditsPerRupee = calculateCreditsPerRupee();
        const calculatedCredits = Math.round(amount * creditsPerRupee);
        setCredits(calculatedCredits);
        setTopUpAmount({ amount, credits: calculatedCredits });
      }
    } else {
      setCredits(0);
      setTopUpAmount({ amount: 0, credits: 0 });
    }
  };

  const handleNextClick = () => {
    if (isOtherSelected) {
      if (customAmount && credits) {
        handlePayment({ amount: parseFloat(customAmount), credits });
      } else {
        alert("Please enter a valid amount.");
      }
    } else if (selectedAmount) {
      handlePayment({ amount: selectedAmount, credits });
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
        <div className="flex items-center justify-center gap-2 mb-10">
          <span className="text-2xl">
            <img src={velocityLogo} className="h-6 sm:h-8" alt="Velocity Logo" />
          </span>
          <span className="text-2xl text-white font-normal font-[Inter]">Velocity</span>
        </div>

        {/* Main Content */}
        <div className="w-full max-w-lg">
          <h1 className="text-2xl mb-8 text-center text-white font-normal font-[Inter]">
            Buy Credits
          </h1>

          {/* Credit Options Grid */}
          <div className="grid grid-cols-3 gap-2 mb-10">
            {creditOptions.map(({ amount, credits }) => (
              <button
                key={amount}
                onClick={() => handleAmountSelect(amount, credits)}
                className={`
                  py-4 px-6 rounded-xl text-xl text-white
                  ${selectedAmount === amount
                    ? 'bg-gray-700 border-2 border-blue-500'
                    : 'bg-gray-800 hover:bg-gray-700'
                  }
                  transition-all duration-200
                `}
                style={{ backgroundColor: '#2B2b2b' }}
              >
                ₹{amount}
              </button>
            ))}
            {/* Other Amount Button */}
            <button
              onClick={handleOtherSelect}
              className={`
                py-4 px-6 rounded-xl text-xl text-white
                ${isOtherSelected
                  ? 'bg-gray-700 border-2 border-blue-500'
                  : 'bg-gray-800 hover:bg-gray-700'
                }
                transition-all duration-200
              `}
              style={{ backgroundColor: '#2B2b2b' }}
            >
              Other
            </button>
          </div>

          {/* Custom Input Fields */}
          {isOtherSelected && (
            <div className="flex flex-col items-center gap-4 mb-8">
              <input
                value={customAmount}
                onChange={(e) => {
                  const value = e.target.value;
                  if (/^\d*\.?\d*$/.test(value)) {
                    handleCustomInputChange(e);
                  }
                }}
                placeholder="Enter amount"
                maxLength="10" // Optional: Set a maximum length for the input
                className="w-full px-4 py-5 rounded-lg bg-gray-800 text-white placeholder-gray-400 text-center flex items-center justify-center"
              />
            </div>

          )}

          {/* Credits Display */}
          <div className="text-center mb-8">
            <h2 className="text-gray-400 mb-4 text-white font-normal font-[Inter]">
              Credits you will get
            </h2>
            <div
              className="inline-block rounded-xl px-6 py-5 text-white font-normal font-[Inter]"
              style={{ backgroundColor: '#2B2b2b' }}
            >
              {credits} Credits
            </div>
          </div>

          {/* Next Button */}
          <button
            onClick={handleNextClick}
            className="w-auto mx-auto block py-5 px-12 rounded-full bg-black border border-blue-500 hover:bg-gray-900 transition-colors duration-200 relative group"
            style={{
              boxShadow: '0 0 20px rgba(59, 130, 246, 0.5)'
            }}
          >
            <span
              className="relative z-10 text-xl font-semibold font-[Inter]"
              style={{ color: 'white' }}
            >
              Next
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default BuyCredits;