import React, { useState, useEffect } from "react";
import { useNavigate } from 'react-router-dom';

const PremiumPlan = ({ planData }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [userData, setUserData] = useState(null);
  const navigate = useNavigate();

  // Decode JWT token to retrieve user information
  const decodeToken = (token) => {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('Token decode error:', error);
      return null;
    }
  };

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const token = localStorage.getItem('token');
        console.log("Raw token:", token); // Debug log

        if (!token) {
          throw new Error('No authentication token found');
        }

        const decodedToken = decodeToken(token);
        console.log("Decoded token:", decodedToken); // Debug log

        if (!decodedToken) {
          throw new Error('Failed to decode token');
        }

        const userId = decodedToken.userId || decodedToken.user_id || decodedToken.sub || localStorage.getItem('userId');
        console.log("Found userId:", userId); // Debug log

        if (!userId) {
          throw new Error('User ID not found in token');
        }

        const response = await fetch(`http://127.0.0.1:3000/api/users/profile/${userId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });

        console.log("API Response status:", response.status); // Debug log

        if (!response.ok) {
          if (response.status === 401) {
            localStorage.clear();
            navigate('/login');
            // throw new Error('Session expired. Please login again.');
          }
          throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        console.log("API Response data:", data); // Debug log

        if (!data.success) {
          throw new Error(data.message || 'Failed to fetch user data');
        }

        setUserData(data.data.user);
        setError(null);

      } catch (err) {
        console.error('Error fetching user data:', err);
        setError(err.message || 'Failed to load user data');
        setUserData(null);
        
        // if (err.message.includes('token') || err.message.includes('Session expired')) {
        //   localStorage.clear();
        //   navigate('/login');
        // }
      }
    };

    fetchUserData();
  }, [navigate]);

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
    if (!userData?.user_id) {
      setError('Please login to upgrade your plan');
      setTimeout(() => {
        navigate('/login');
      }, 2000);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch(`http://127.0.0.1:3000/api/plans/${userData.user_id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          plan_id: 2
        })
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.clear();
          navigate('/login');
          // throw new Error('Session expired. Please login again.');
        }
        throw new Error(data.message || 'Failed to upgrade plan');
      }

      setError(null);
      alert('Plan upgraded successfully!');
      window.location.reload();

    } catch (err) {
      setError(err.message);
      if (err.message.includes('authentication') || err.message.includes('Session expired')) {
        localStorage.clear();
        navigate('/login');
      }
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
        disabled={loading || !userData}
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