import React from 'react'
import circuit from "../../assets/circuit.png"
import cardbg from "../../assets/howitworkscard.png"

const HowItWorksCard = () => {
  return (
    <div className='w-[350px]' style={{ backgroundImage: `url(${cardbg})`, backgroundRepeat: "no-repeat", backgroundSize: "cover", backgroundPosition: "center"}}>
      <div className='py-10'>
        <div className='flex items-center'>
          <img src={circuit} alt="Circuit Icon" />
          <span className='text-primary'>Choose your AI platform</span>
        </div>
        <div>
          <span className='text-[#999999]'>Choose your desired AI platform
          (e.g., GPT, DALL-E)</span>
        </div>
      </div>
    </div>
  )
}

export default HowItWorksCard