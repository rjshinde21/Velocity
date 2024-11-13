import React from "react";

const FreePlan = ({ planData }) => {
  if (!planData) return null;

  const PlanDot = () => (
    <svg
      className="flex-shrink-0 w-2 h-2 text-gray-400 dark:text-gray-500"
      aria-hidden="true"
      xmlns="http://www.w3.org/2000/svg"
      fill="currentColor"
      viewBox="0 0 20 20"
    >
      <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5Z" />
    </svg>
  );

  const renderFeatureItem = (feature, isStrikethrough = false) => (
    <li className={`flex sm:block md:flex items-center ${isStrikethrough ? 'line-through decoration-gray-500' : ''}`}>
      <PlanDot />
      <span className={`text-base font-normal leading-tight text-gray-500 dark:text-gray-400 ms-3 ${isStrikethrough ? 'line-through' : ''}`}>
        {feature}
      </span>
    </li>
  );

  return (
    <div className="w-full max-w-lg p-4 border border-[#2C2C2C] font-[Inter] rounded-lg shadow sm:p-12 bg-[#111111] hover:scale-105 transition-all duration-200">
      <div className="flex md:flex-col justify-between md:justify-start items-center md:items-start">
        <h5 className="mb-0 sm:mb-4 text-md sm:text-xl font-medium text-[#757575]">
          {planData.name || 'Free plan'}
        </h5>
        <div className="flex items-baseline text-[#757575]">
          <span className="text-3xl sm:text-5xl font-semibold">₹</span>
          <span className="text-4xl sm:text-5xl font-extrabold tracking-tight">
            {planData.price || '00'}
          </span>
          <span className="ms-1 text-xl font-normal text-gray-500 dark:text-gray-400">
            /month
          </span>
        </div>
      </div>
      
      <ul
        role="list"
        className="space-y-5 my-3 sm:my-7 grid grid-cols-2 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-1"
      >
        {planData.features?.map((feature, index) => (
          <React.Fragment key={index}>
            {index < 2 && renderFeatureItem(feature)}
          </React.Fragment>
        ))}
        
        {/* Strikethrough features */}
        {planData.disabledFeatures?.map((feature, index) => (
          <React.Fragment key={`disabled-${index}`}>
            {renderFeatureItem(feature, true)}
          </React.Fragment>
        ))}
      </ul>
      
      <button
        type="button"
        className="text-white bg-[#2C2C2C] hover:bg-[#535353] font-medium rounded-[30px] text-sm px-5 py-2.5 inline-flex justify-center w-full text-center transition-colors duration-500 ease-in-out"
        onClick={planData.onSignUp}
      >
        {planData.buttonText || 'Sign Up'}
      </button>
    </div>
  );
};

export default FreePlan;