// Pricing.js
import React, { useEffect, useState } from 'react';
import FreePlan from "./FreePlan";
import PremiumPlan from "./PremiumPlan";
import CustomPlan from './CustomPlan';

const Pricing = ({isLoggedIn}) => {
  const [freePlanData, setFreePlanData] = useState(null);
  const [premiumPlanData, setPremiumPlanData] = useState(null);
  const [customPlanData, setCustomPlanData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isMonthly, setIsMonthly] = useState(true);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const token = localStorage.getItem('token');
        console.log("usertoken:"+token);
        
        const freeResponse = 
          {
            "success": true,
            "data": {
                "plan_id": 1,
                "plan_name": "freeee plan",
                "token_received": 100,
                "cost": "0.00",
                "active_users": 4
            }
          }
          const premiumResponse = {
            "success": true,
            "data": {
                "plan_id": 2,
                "plan_name": "premium plannn",
                "token_received": 100,
                "cost": "299.00",
                "active_users": 6
            }
        }    
        const customResponse = 
          {
            "success": true,
            "data": {
                "plan_id": 3,
                "plan_name": "custommm plan",
                "token_received": 100,
                "cost": "0.00",
                "active_users": 4
            }
          }    

        const { data: freeData } = freeResponse;
        const { data: premiumData } = premiumResponse;
        const { data: customData } = customResponse;

        const transformedFreePlan = {
          name: freeData.plan_name,
          price: freeData.cost,
          tokens: freeData.token_received,
          features: [
            "Unlimited usage",
            "Usable up to 5 times",
          ],
          disabledFeatures: [
            "5 credits per use",
            "10 credits per use",
            "Included"
          ],
          activeUsers: freeData.active_users
        };

        const transformedPremiumPlan = {
          name: premiumData.plan_name,
          price: premiumData.cost,
          tokens: premiumData.token_received,
          features: [
            "Unlimited usage",
            "Unlimited usage with credits",
            "5 credits per use",
            "10 credits per use",
            "Include"
          ],
          disabledFeatures: [],
          activeUsers: premiumData.active_users
        };

        const transformedCustomPlan = {
          name: customData.plan_name,
          price: customData.cost,
          tokens: customData.token_received,
          features: [
            "Unlimited usage",
            "Unlimited usage with credits",
            "5 credits per use",
            "10 credits per use",
            "Include"
          ],
          disabledFeatures: [],
          activeUsers: customData.active_users
        };

        setFreePlanData(transformedFreePlan);
        setPremiumPlanData(transformedPremiumPlan);
        setCustomPlanData(transformedCustomPlan)
      } catch (err) {
        setError(err.message);
        console.error('Error fetching plans:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchPlans();
  }, []);

  return (
    <div className="flex flex-col items-center">
      <h3 className="bg-gradient-to-r from-[#DADADA] to-[#999999] bg-clip-text text-transparent text-3xl sm:text-4xl p-4 sm:p-10 font-[Amenti]">
        Explore our Plans
      </h3>

      <div className="flex items-center justify-center space-x-2 bg-[#161616] p-1 rounded-lg w-fit border border-[#ffffff]/10">
      {/* Monthly Button */}
      <button
        onClick={() => setIsMonthly(true)}
        className={`px-4 py-2 rounded-lg ${
          isMonthly ? 'bg-gradient-to-b from-[#008ACB] to-[#005076] text-white' : 'bg-transparent text-gray-400'
        } focus:outline-none`}
      >
        Monthly
      </button>
      
      {/* Annually Button */}
      <button
        onClick={() => setIsMonthly(false)}
        className={`px-4 py-2 rounded-lg ${
          !isMonthly ? 'bg-gradient-to-b from-[#008ACB] to-[#005076] text-white' : 'bg-transparent text-gray-400'
        } focus:outline-none`}
      >
        Annually
      </button>
    </div>

      <div className="flex flex-col lg:flex-row gap-4 sm:gap-8 px-4 py-8 lg:justify-center">
        {loading ? (
          <div className="flex justify-center items-center p-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#008ACB]" />
          </div>
        ) : error ? (
          <div className="text-red-500 text-center">{error}</div>
        ) : (
          <div className="flex flex-col lg:flex-row gap-4 sm:gap-8">
            <div className="flex-grow-0">
              <FreePlan planData={freePlanData} isLoggedIn={isLoggedIn}/>
            </div>
            <div className="flex-grow">
              <PremiumPlan planData={premiumPlanData} isMonthly={isMonthly} />
            </div>
            <div className="flex-grow-0">
              <CustomPlan planData={customPlanData} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Pricing;
