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

        const [freeResponse, premiumResponse] = await Promise.all([
          fetch('http://127.0.0.1:3000/api/plans/1', {
            method: 'GET',
            headers: headers
          }),
          fetch('http://127.0.0.1:3000/api/plans/2', {
            method: 'GET',
            headers: headers
          })
        ]);

        if (!freeResponse.ok || !premiumResponse.ok) {
          throw new Error(`Failed to fetch plans: ${freeResponse.statusText}`);
        }

        const { data: freeData } = await freeResponse.json();
        const { data: premiumData } = await premiumResponse.json();

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
        <div className="w-full max-w-3xl py-4 font-[Inter] rounded-lg shadow sm:py-12">
          <div className="flex md:flex-col justify-between md:justify-start items-center md:items-start">
            <h5 className="leading-tight text-[#999999] font-bold ms-3 mb-10">
              Features
            </h5>
          </div>
          <ul role="list" className="space-y-5 my-3 sm:my-7 grid grid-cols-2 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-2">
            <li className="flex items-center sm:block md:flex">
              <span className="text-base font-normal leading-tight text-[#999999] dark:text-gray-400 ms-3">
                Base Level Prompt Enhancement
              </span>
            </li>
            <li className="flex sm:block md:flex">
              <span className="text-base font-normal leading-tight text-[#999999] dark:text-gray-400 ms-3">
                Advanced Features
              </span>
            </li>
            <li className="flex sm:block md:flex">
              <span className="text-base font-normal leading-tight text-[#999999] dark:text-gray-400 ms-3">
                Advanced Prompt Customization
              </span>
            </li>
            <li className="flex sm:block md:flex">
              <span className="text-base font-normal leading-tight text-[#999999] ms-3">
                Image to Prompt Feature
              </span>
            </li>
            <li className="flex sm:block md:flex">
              <span className="text-base font-normal leading-tight text-[#999999] ms-3">
                Storage of Prompts
              </span>
            </li>
          </ul>
        </div>
        
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
          </>
        )}
      </div>
    </div>
  );
};

export default Pricing;