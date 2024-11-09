import React from "react";

const PricingCard = () => {
  return (
    <div class="w-full max-w-sm p-4 border border-[#2C2C2C] font-[Inter] hover:border-[#004565] rounded-lg shadow sm:p-12 bg-[#111111] hover:scale-105 transition-all duration-200">
      <div className="flex md:flex-col justify-between md:justify-start items-center md:items-start">
      <h5 class="mb-0 sm:mb-4 text-md sm:text-xl font-medium text-[#757575]">
        Standard plan
      </h5>
      <div class="flex items-baseline text-[#757575]">
        <span class="text-3xl sm:text-5xl font-semibold">$</span>
        <span class="text-4xl sm:text-5xl font-extrabold tracking-tight">49</span>
        <span class="ms-1 text-xl font-normal text-gray-500 dark:text-gray-400">
          /month
        </span>
      </div>
      </div>
      <ul role="list" class="space-y-5 my-3 sm:my-7 grid grid-cols-2 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-2">
  <li class="flex items-center sm:block md:flex">
    <svg
      class="flex-shrink-0 w-4 h-4 text-[#008ACB] dark:text-blue-500"
      aria-hidden="true"
      xmlns="http://www.w3.org/2000/svg"
      fill="currentColor"
      viewBox="0 0 20 20"
    >
      <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5Zm3.707 8.207-4 4a1 1 0 0 1-1.414 0l-2-2a1 1 0 0 1 1.414-1.414L9 10.586l3.293-3.293a1 1 0 0 1 1.414 1.414Z" />
    </svg>
    <span class="text-base font-normal leading-tight text-gray-500 dark:text-gray-400 ms-3">
      2 team members
    </span>
  </li>
  <li class="flex sm:block md:flex">
    <svg
      class="flex-shrink-0 w-4 h-4 text-[#008ACB] dark:text-blue-500"
      aria-hidden="true"
      xmlns="http://www.w3.org/2000/svg"
      fill="currentColor"
      viewBox="0 0 20 20"
    >
      <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5Zm3.707 8.207-4 4a1 1 0 0 1-1.414 0l-2-2a1 1 0 0 1 1.414-1.414L9 10.586l3.293-3.293a1 1 0 0 1 1.414 1.414Z" />
    </svg>
    <span class="text-base font-normal leading-tight text-gray-500 dark:text-gray-400 ms-3">
      20GB Cloud storage
    </span>
  </li>
  <li class="flex sm:block md:flex">
    <svg
      class="flex-shrink-0 w-4 h-4 text-[#008ACB] dark:text-blue-500"
      aria-hidden="true"
      xmlns="http://www.w3.org/2000/svg"
      fill="currentColor"
      viewBox="0 0 20 20"
    >
      <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5Zm3.707 8.207-4 4a1 1 0 0 1-1.414 0l-2-2a1 1 0 0 1 1.414-1.414L9 10.586l3.293-3.293a1 1 0 0 1 1.414 1.414Z" />
    </svg>
    <span class="text-base font-normal leading-tight text-gray-500 dark:text-gray-400 ms-3">
      Integration help
    </span>
  </li>
  <li class="flex line-through decoration-gray-500 sm:block md:flex">
    <svg
      class="flex-shrink-0 w-4 h-4 text-gray-400 dark:text-gray-500"
      aria-hidden="true"
      xmlns="http://www.w3.org/2000/svg"
      fill="currentColor"
      viewBox="0 0 20 20"
    >
      <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5Zm3.707 8.207-4 4a1 1 0 0 1-1.414 0l-2-2a1 1 0 0 1 1.414-1.414L9 10.586l3.293-3.293a1 1 0 0 1 1.414 1.414Z" />
    </svg>
    <span class="text-base font-normal leading-tight text-gray-500 ms-3">
      Sketch Files
    </span>
  </li>
</ul>



      <button
  type="button"
  class="text-white bg-[#2C2C2C] hover:bg-[#535353] font-medium rounded-[30px] text-sm px-5 py-2.5 inline-flex justify-center w-full text-center transition-colors duration-500 ease-in-out"
>
  Choose plan
</button>

    </div>
  );
};

export default PricingCard;
