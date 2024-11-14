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

  const listItems = ["Customized usage and features tailored to business needs", "Advanced integrations available upon request"]

  return (
    <div className="w-full max-w-xs p-6 font-[Inter] rounded-[32px] shadow sm:p-8 hover:scale-105 transition-all duration-200" style={{
      backgroundImage: 'linear-gradient(to bottom right, #008ACB1A 0%, #008ACB1A 50%, #000000 100%)',
    }}>
      <div className="flex md:flex-col justify-between md:justify-start items-center md:items-start">
        <div className="flex flex-col">
        <h5 className="mb-0 sm:mb-1 text-xl font-[Inter] text-[#ffffff]">
          {/* {planData.name || 'Free plan'} */}
          Enterprise
        </h5>
        <h5 className="mb-0 sm:mb-8 text-sm font-medium text-[#757575]">
          {/* {planData.name || 'Built for teams and businesses'} */}
          Built for teams and businesses
        </h5>
        </div>
        <div className="flex items-baseline text-[#ffffff]">
          <span className="text-[32px] font-semibold"></span>
          <span className="text-[32px] tracking-tight text-right leading-tight">
            {/* {planData.price || '00'} */}
            Custom Pricing
          </span>
          <span className="ms-1 text-xl font-normal text-gray-500 dark:text-gray-400">
            
          </span>
        </div>
      </div>
      <button
        type="button"
        className="text-white my-4 sm:my-10 font-medium rounded-xl text-sm px-5 py-2.5 inline-flex justify-center  w-full text-center transition-colors duration-500 ease-in-out border border-[#ffffff]/10"
        style={{
          backgroundImage: 'linear-gradient(to bottom, #008ACB1A 0%, #000000 100%)',
        }}
        onClick={planData.onSignUp}
      >
        {planData.buttonText || 'Contact Sales'}
      </button>
      
      <ul
        role="list"
        className="py-4 sm:py-10 my-3 sm:my-0 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-1 border-t border-[#ffffff]/20"
      >
        <li class="flex items-center mb-4">
<span class="text-base font-normal leading-tight text-primary dark:text-gray-400">What you will get</span>
</li>
{listItems.map((item)=>(
    <li class="flex items-center mb-4 text-[#ffffff]/80">
<svg class="flex-shrink-0 w-4 h-4 text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 20">
  <circle cx="10" cy="10" r="9.5" stroke="white" stroke-width="1" fill="transparent"/>
  <path d="M7 10l1.5 1.5L13 8" stroke="white" stroke-width="1" fill="none"/>
</svg>
<span class="text-sm font-normal leading-tight text-[#ffffff]/80 dark:text-gray-400 ms-3">{item}</span>
</li>
))}
        {/* {planData.features?.map((feature, index) => (
          <React.Fragment key={index}>
            {index < 2 && renderFeatureItem(feature)}
          </React.Fragment>
        ))} */}
        
        {/* Strikethrough features */}
        {/* {planData.disabledFeatures?.map((feature, index) => (
          <React.Fragment key={`disabled-${index}`}>
            {renderFeatureItem(feature, true)}
          </React.Fragment>
        ))} */}
      </ul>
      
    </div>
  );
};

export default FreePlan;