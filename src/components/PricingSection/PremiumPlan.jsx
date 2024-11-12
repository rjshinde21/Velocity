import React from "react";

const PremiumPlan = () => {
  return (
    <div class="w-full max-w-sm p-4 border border-[#B78629] font-[Inter] rounded-lg shadow sm:p-12 bg-gradient-to-r from-[#B78629]/10 to-[#FCC101]/10 hover:scale-105 transition-all duration-200">
      <div className="flex md:flex-col justify-between md:justify-start items-center md:items-start">
        <h5 class="mb-0 sm:mb-4 text-md sm:text-xl font-medium bg-gradient-premium">
          Premium plan
        </h5>
        <div class="flex items-baseline bg-gradient-premium">
          <span class="text-3xl sm:text-5xl font-semibold">₹</span>
          <span class="text-4xl sm:text-5xl font-extrabold tracking-tight">
            149
          </span>
          <span class="ms-1 text-xl font-normal bg-gradient-premium">
            /month
          </span>
        </div>
      </div>
      <ul
        role="list"
        class="space-y-5 my-3 sm:my-7 grid grid-cols-2 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-1"
      >
        <li class="flex items-center sm:block md:flex">
<svg
  class="flex-shrink-0 w-2 h-2 text-[#B78629] dark:bg-gradient-premium"
  aria-hidden="true"
  xmlns="http://www.w3.org/2000/svg"
  fill="currentColor"
  viewBox="0 0 20 20"
>
  <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5Z" />
</svg>
          <span class="text-base font-normal leading-tight bg-gradient-premium ms-3">
            Unlimited usage
          </span>
        </li>
        <li class="flex sm:block md:flex items-center">
<svg
  class="flex-shrink-0 w-2 h-2 text-[#B78629] dark:bg-gradient-premium"
  aria-hidden="true"
  xmlns="http://www.w3.org/2000/svg"
  fill="currentColor"
  viewBox="0 0 20 20"
>
  <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5Z" />
</svg>
          <span class="text-base font-normal leading-tight bg-gradient-premium ms-3">
          Unlimited usage with credits
          </span>
        </li>
        <li class="flex sm:block md:flex items-center">
<svg
  class="flex-shrink-0 w-2 h-2 text-[#B78629] dark:bg-gradient-premium"
  aria-hidden="true"
  xmlns="http://www.w3.org/2000/svg"
  fill="currentColor"
  viewBox="0 0 20 20"
>
  <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5Z" />
</svg>
          <span class="text-base line-through font-normal leading-tight bg-gradient-premium ms-3">
            5 credits per use
          </span>
        </li>
        <li class="flex line-through decoration-[#B78629] sm:block md:flex items-center">

<svg
  class="flex-shrink-0 w-2 h-2 text-[#B78629] dark:bg-gradient-premium"
  aria-hidden="true"
  xmlns="http://www.w3.org/2000/svg"
  fill="currentColor"
  viewBox="0 0 20 20"
>
  <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5Z" />
</svg>

          <span class="text-base line-through font-normal leading-tight bg-gradient-premium ms-3">
            10 credits per use
          </span>
        </li>
        <li class="flex line-through decoration-[#B78629] sm:block md:flex items-center">
        <svg
  class="flex-shrink-0 w-2 h-2 text-[#B78629] dark:bg-gradient-premium"
  aria-hidden="true"
  xmlns="http://www.w3.org/2000/svg"
  fill="currentColor"
  viewBox="0 0 20 20"
>
  <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5Z" />
</svg>
          <span class="text-base line-through font-normal leading-tight bg-gradient-premium ms-3">
            Included
          </span>
        </li>
      </ul>

      <button
        type="button"
        class="text-black bg-gradient-to-b from-[#B78629] to-[#FCC101] font-medium rounded-[30px] text-sm px-5 py-2.5 inline-flex justify-center w-full text-center transition-colors duration-500 ease-in-out"
      >
        Try Now
      </button>
    </div>
  );
};

export default PremiumPlan;
