import { useState, useEffect } from 'react';
import FreePlan from "./FreePlan";
import PremiumPlan from "./PremiumPlan";

const Pricing = () => {
  const [freePlanData, setFreePlanData] = useState(null);
  const [premiumPlanData, setPremiumPlanData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const token = localStorage.getItem('token');
        
        const headers = {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        };

        // const [freeResponse, premiumResponse] = await Promise.all([
        //   fetch('http://127.0.0.1:3000/api/plans/1', {
        //     method: 'GET',
        //     headers: headers
        //   }),
        //   fetch('http://127.0.0.1:3000/api/plans/2', {
        //     method: 'GET',
        //     headers: headers
        //   })
        // ]);
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
        // if (!freeResponse.ok || !premiumResponse.ok) {
        //   throw new Error(`Failed to fetch plans: ${freeResponse.statusText}`);
        // }

        const { data: freeData } =  freeResponse
        const { data: premiumData } =premiumResponse;

        // Transform API data to match component needs
        const transformedFreePlan = {
          name: freeData.plan_name,
          price: freeData.cost,
          tokens: freeData.token_received,
          features: [
            "Unlimited usage",
            // `${freeData.token_received} tokens per month`,
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
            // `${premiumData.token_received} tokens per month`,
            "Unlimited usage with credits",

            "5 credits per use",
            "10 credits per use",
            "Include"
          ],
          disabledFeatures: [],
          activeUsers: premiumData.active_users
        };

        setFreePlanData(transformedFreePlan);
        setPremiumPlanData(transformedPremiumPlan);
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
      <div className="flex flex-col sm:flex-row gap-4 sm:gap-8 p-4">
        
        
        {loading ? (
          <div className="flex justify-center items-center p-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#008ACB]" />
          </div>
        ) : error ? (
          <div className="text-red-500 text-center">{error}</div>
        ) : (
          <>
            <FreePlan planData={freePlanData} />
            <PremiumPlan planData={premiumPlanData} />
            <FreePlan planData={freePlanData} />
          </>
        )}
      </div>
    </div>
  );
};

export default Pricing;