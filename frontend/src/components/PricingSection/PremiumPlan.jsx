import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const PremiumPlan = ({ planData, isMonthly }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [userData, setUserData] = useState(null);
  const [tokenInfo, setTokenInfo] = useState(null);
  const navigate = useNavigate();

  // Decode JWT token to retrieve user information
  const decodeToken = (token) => {
    try {
      const base64Url = token.split(".")[1];
      const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split("")
          .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
          .join("")
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error("Token decode error:", error);
      return null;
    }
  };

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const token = localStorage.getItem("token");
        console.log("Raw token:", token); // Debug log

        if (!token) {
          throw new Error("No authentication token found");
        }

        const decodedToken = decodeToken(token);
        console.log("Decoded token:", decodedToken); // Debug log

        if (!decodedToken) {
          throw new Error("Failed to decode token");
        }

        const userId =
          decodedToken.userId ||
          decodedToken.user_id ||
          decodedToken.sub ||
          localStorage.getItem("userId");
        console.log("Found userId:", userId); // Debug log

        if (!userId) {
          throw new Error("User ID not found in token");
        }

        const response = await fetch(
          `http://127.0.0.1:3000/api/users/profile/${userId}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              Accept: "application/json",
              "Content-Type": "application/json",
            },
          }
        );

        console.log("API Response status:", response.status); // Debug log

        if (!response.ok) {
          if (response.status === 401) {
            localStorage.clear();
            navigate("/login");
            throw new Error("Session expired. Please login again.");
          }
          throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        console.log("API Response data:", data); // Debug log

        if (!data.success) {
          throw new Error(data.message || "Failed to fetch user data");
        }

        setUserData(data.data.user);
        setError(null);
      } catch (err) {
        console.error("Error fetching user data:", err);
        setError(err.message || "Failed to load user data");
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
    <li
      className={`flex sm:block md:flex items-center ${
        isStrikethrough ? "line-through decoration-[#B78629]" : ""
      }`}
    >
      <PlanDot />
      <span
        className={`text-base font-normal leading-tight bg-gradient-premium ms-3 ${
          isStrikethrough ? "line-through" : ""
        }`}
      >
        {feature}
      </span>
    </li>
  );

  const handleUpgrade = async () => {
    if (!userData?.user_id) {
      setError("Please login to upgrade your plan");
      alert("Please login to upgrade your plan. Redirecting to login...");
      setTimeout(() => {
        navigate("/login");
      }, 2000);
      return;
    }
  
    setLoading(true);  // Start loading when the upgrade process begins
    setError(null);
  
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        throw new Error("Authentication required");
      }
  
      // Step 1: Update the plan
      const planResponse = await fetch(
        `http://127.0.0.1:3000/api/plans/${userData.user_id}`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({
            plan_id: 2, // Set the plan_id to Premium
          }),
        }
      );
  
      const planData = await planResponse.json();
  
      if (!planResponse.ok) {
        if (planResponse.status === 401) {
          localStorage.clear();
          navigate("/login");
          throw new Error("Session expired. Please login again.");
        }
        throw new Error(planData.message || "Failed to upgrade plan");
      }
  
      // Step 2: Fetch the current token data
      const currentDataResponse = await fetch(
        `http://127.0.0.1:3000/api/token-types/${userData.user_id}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
  
      if (!currentDataResponse.ok) {
        const errorData = await currentDataResponse.json();
        throw new Error(errorData.message || "Failed to fetch current token data");
      }
  
      const currentData = await currentDataResponse.json();
      console.log("Current Token Data:", currentData); // Debug log
  
      const { token_received = 0, tokens_used = 0 } = currentData.data;
  
      // Step 3: Fetch the plan's token_received value (100 for Premium plan)
      const planTokenReceivedResponse = await fetch(
        `http://127.0.0.1:3000/api/plans/2`, // Assuming `2` is the Premium plan
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
  
      const planTokenData = await planTokenReceivedResponse.json();
      console.log("planTokenData:"+planTokenData);
  
      if (!planTokenReceivedResponse.ok) {
        const errorData = await planTokenReceivedResponse.json();
        throw new Error(errorData.message || "Failed to fetch plan data");
      }
  
      const { token_received: planTokenReceived = 0 } = planTokenData.data;
      const { token_received_yearly: planTokenReceivedYearly = 0 } = planTokenData.data;
  
      // Step 4: Calculate the updated token value
    const additionalTokens = isMonthly ? planTokenReceived : planTokenReceivedYearly;
    const updatedTokenReceived = token_received + additionalTokens;
  
      // Step 5: Update the token data with the new value
      const tokenResponse = await fetch(
        `http://127.0.0.1:3000/api/token-types/${userData.user_id}`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            token_received: updatedTokenReceived,
            tokens_used: tokens_used, // Retain tokens_used as it is
          }),
        }
      );
  
      const tokenData = await tokenResponse.json();
  
      if (!tokenResponse.ok) {
        throw new Error(tokenData.message || "Failed to update tokens");
      }
  
      setError(null);
      alert("Plan and tokens upgraded successfully!");
      window.location.reload(); // Reload the page to reflect the changes
  
    } catch (err) {
      console.error("Upgrade error:", err);
      setError(err.message);
  
      if (
        err.message.includes("authentication") ||
        err.message.includes("Session expired")
      ) {
        localStorage.clear();
        navigate("/login");
      }
  
    } finally {
      setLoading(false); // Stop loading once the process is completed
    }
  };
  
  
  

  if (!planData) return null;

  const listItems = [
    "Unlimited Base Level Prompt Enhancement",
    "Advanced Features with flexible credit use",
    "Advanced Prompt Customization for 5 credits per use",
    "Image to Prompt magic for 10 credits per use",
    "Storage for all your prompts",
  ];

  return (
    <div className="w-full max-w-sm border border-[#008ACB52] p-6 font-[Inter] rounded-[32px] shadow sm:p-8 hover:scale-105 transition-all duration-200 bg-gradient-to-t from-[rgba(0,138,203,0.12)] via-[rgba(0,138,203,0.04)] to-[rgba(0,138,203,0.14)] backdrop-blur-[84px] ">
      <div className="flex md:flex-col justify-between md:justify-start items-center md:items-start">
      <div className="flex flex-col">
        <h5 className="mb-0 sm:mb-1 text-xl font-[Inter] text-[#ffffff]">
          {planData.name || 'Premium'}
          {/* Premium */}
        </h5>
        <h5 className="mb-0 sm:mb-4 text-sm font-medium text-[#757575]">
          {/* {planData.name || 'Limited but powerful'} */}
          Unleash your creativity
        </h5>
        </div>
        <div className="flex items-baseline text-[#ffffff]">
          <span className="text-[32px] font-semibold">$</span>
          <span className="text-[32px] sm:text-[48px] tracking-tight">
            {/* {planData.price || '00'} */}
            {isMonthly ? planData.price : planData.price_yearly}
          </span>
          <span className="ms-1 text-sm font-normal text-gray-500 dark:text-gray-400">
            /{isMonthly ? "month" : "year"}
          </span>
        </div>
      </div>
      <button
        type="button"
        className="text-white my-4 sm:my-9 font-medium rounded-xl text-sm px-5 py-2.5 inline-flex justify-center w-full text-center transition-colors duration-500 ease-in-out"
        style={{
          backgroundImage:
            "linear-gradient(to bottom, #008ACB 0%, #005076 100%)",
        }}
        onClick={handleUpgrade}
      >
        {planData.buttonText || "Get Started"}
      </button>

      <ul
        role="list"
        className="py-4 sm:py-10 my-3 sm:my-0 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-1 border-t border-[#ffffff]/20"
      >
        <li class="flex items-center mb-4">
          <span class="text-base font-normal leading-tight text-primary dark:text-gray-400">
            What you will get
          </span>
        </li>
        {listItems.map((item) => (
          <li class="flex items-center mb-4 text-[#ffffff]/80">
            <svg class="flex-shrink-0 w-4 h-4 text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 20">
  <circle cx="10" cy="10" r="9.5" stroke="white" stroke-width="1" fill="transparent"/>
  <path d="M7 10l1.5 1.5L13 8" stroke="white" stroke-width="1" fill="none"/>
</svg>

            <span class="text-sm font-normal leading-tight text-[#ffffff]/80 dark:text-gray-400 ms-3">
              {item}
            </span>
          </li>
        ))}
        {/* {planData.features?.map((feature, index) => (
          <React.Fragment key={index}>
            {index < 5 && renderFeatureItem(feature)}
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

export default PremiumPlan;
