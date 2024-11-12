import FreePlan from "./FreePlan";
import PremiumPlan from "./PremiumPlan";

const Pricing = () => {  

  return (
    <div className="flex flex-col items-center">
      <h3 className="bg-gradient-to-r from-[#DADADA] to-[#999999] bg-clip-text text-transparent text-3xl sm:text-4xl p-4 sm:p-10 font-[Amenti]">Explore our Plans</h3>
      <div className="flex flex-col sm:flex-row gap-4 sm:gap-8 p-4">
        <div class="w-full max-w-3xl py-4 font-[Inter] rounded-lg shadow sm:py-12">
      <div className="flex md:flex-col justify-between md:justify-start items-center md:items-start">
      <h5 class="leading-tight text-[#999999] font-bold ms-3 mb-10">
        Features
      </h5>
      </div>
      <ul role="list" class="space-y-5 my-3 sm:my-7 grid grid-cols-2 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-2">
  <li class="flex items-center sm:block md:flex">

    <span class="text-base font-normal leading-tight text-[#999999] dark:text-gray-400 ms-3">
      Base Level Prompt Enhancement
    </span>
  </li>
  <li class="flex sm:block md:flex">
    <span class="text-base font-normal leading-tight text-[#999999] dark:text-gray-400 ms-3">
    Advanced Features
    </span>
  </li>
  <li class="flex sm:block md:flex">
    <span class="text-base font-normal leading-tight text-[#999999] dark:text-gray-400 ms-3">
    Advanced Prompt Customization
    </span>
  </li>
  <li class="flex sm:block md:flex">
    <span class="text-base font-normal leading-tight text-[#999999] ms-3">
    Image to Prompt Feature
    </span>
  </li>
  <li class="flex sm:block md:flex">
    <span class="text-base font-normal leading-tight text-[#999999] ms-3">
    Storage of Prompts
    </span>
  </li>
</ul>
    </div>
        <FreePlan />
        <PremiumPlan />
      </div>
    </div>
  );
};

export default Pricing;
