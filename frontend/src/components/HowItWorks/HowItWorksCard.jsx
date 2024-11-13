import React from 'react'
import cardbg from "../../assets/howitworkscard.png"

const HowItWorksCard = () => {
  return (
    <div
        className="w-[300px] h-[150px] flex flex-col justify-center items-center p-6 text-white bg-cover bg-center rounded-md shadow-lg"
      style={{ backgroundImage: `url(${cardbg})` }}  // Replace with your image URL
      >
        <div className="flex flex-col items-center">
          <div className="text-2xl font-semibold mb-2">Choose your AI platform</div>
          <p className="text-sm text-gray-300 text-center">
            Choose your desired AI platform (e.g., GPT, DALL-E)
          </p>
        </div>
      </div>
  )
}

export default HowItWorksCard