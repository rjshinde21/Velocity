import React, { useState } from "react";


const PremiumPlan = ({ planData }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);


  const PlanDot = () => (
    <svg
      className="flex-shrink-0 w-2 h-2 text-[#B78629] dark:bg-gradient-premium"
      aria-hidden="true"
      xmlns="http://www.w3.org/2000/svg"
      fill="currentColor"
      viewBox="0 0 20 20"
    >
      <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5Z" />
    </svg>
  );

  const renderFeatureItem = (feature, isStrikethrough = false) => (
    <li className={`flex sm:block md:flex items-center ${isStrikethrough ? 'line-through decoration-[#B78629]' : ''}`}>
      <PlanDot />
      <span className={`text-base font-normal leading-tight bg-gradient-premium ms-3 ${isStrikethrough ? 'line-through' : ''}`}>
        {feature}
      </span>
    </li>
  );

  const handleUpgrade = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://127.0.0.1:3000/api/plans/31', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to upgrade plan');
      }

      // Show success alert
      alert('Plan updated successfully!');
      
      // Refresh the page or update UI
      window.location.reload(); // or router.reload() if using Next.js
      
    } catch (err) {
      setError(err.message);
      alert('Failed to upgrade plan: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!planData) return null;

  return (
    <div className="w-full max-w-lg p-4 border border-[#B78629] font-[Inter] rounded-lg shadow sm:p-12 bg-gradient-to-r from-[#B78629]/10 to-[#FCC101]/10 hover:scale-105 transition-all duration-200">
      <div className="flex md:flex-col justify-between md:justify-start items-center md:items-start">
        <h5 className="mb-0 sm:mb-4 text-md sm:text-xl font-medium bg-gradient-premium">
          {planData.name || 'Premium plan'}
        </h5>
        <div className="flex items-baseline bg-gradient-premium">
          <span className="text-3xl sm:text-5xl font-semibold">₹</span>
          <span className="text-4xl sm:text-5xl font-extrabold tracking-tight">
            {planData.price || '149'}
          </span>
          <span className="ms-1 text-xl font-normal bg-gradient-premium">
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
            {index < 5 && renderFeatureItem(feature)}
          </React.Fragment>
        ))}
        
        {planData.disabledFeatures?.map((feature, index) => (
          <React.Fragment key={`disabled-${index}`}>
            {renderFeatureItem(feature, true)}
          </React.Fragment>
        ))}
      </ul>
      
      <button
        type="button"
        className={`text-black bg-gradient-to-b from-[#B78629] to-[#FCC101] font-medium rounded-[30px] text-sm px-5 py-2.5 inline-flex justify-center w-full text-center transition-colors duration-500 ease-in-out ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
        onClick={handleUpgrade}
        disabled={loading}
      >
        {loading ? 'Upgrading...' : 'Try Now'}
      </button>
      
      {error && (
        <p className="text-red-500 text-sm mt-2 text-center">{error}</p>
      )}
    </div>
  );
};

export default PremiumPlan;