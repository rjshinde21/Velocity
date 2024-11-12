import React from 'react'
import cardbg from "../../assets/howitworkscard.png"
import circuit from "../../assets/circuit.png"
import mask from "../../assets/Mask.png"

const HowItWorks = () => {
  return (
    <div className='' style={{ backgroundImage: `url(${mask})`, backgroundRepeat: "no-repeat", backgroundSize: "cover"}}>
        <h3 className="bg-gradient-to-r from-[#DADADA] to-[#999999] bg-clip-text text-transparent text-3xl sm:text-4xl p-8 sm:p-12 font-[Amenti] flex justify-center">How It Works</h3>
        <div className="flex flex-col sm:flex-row justify-center items-center gap-4 sm:gap-10 pb-16">
      <div
        className="w-[300px] h-[150px] flex flex-col justify-center items-center p-6 text-white bg-cover bg-center rounded-md shadow-lg"
      style={{ backgroundImage: `url(${cardbg})`, backgroundSize: "cover" }} 
      >
        <div className="flex flex-col justify-center text-left">
          <div className="font-semibold mb-2 flex items-center"><img className='w-7 h-7 mr-3' src={circuit} alt="Prompt Icon" /><span className='text-md'>Choose your AI platform</span></div>
          <p className="text-sm text-[#999999] text-left">
            Choose your desired AI platform (e.g., GPT, DALL-E)
          </p>
        </div>
      </div>

      <div
        className="w-[300px] h-[150px] flex flex-col justify-center items-center p-6 text-white bg-cover bg-center rounded-md shadow-lg"
      style={{ backgroundImage: `url(${cardbg})`, backgroundSize: "cover" }} 
      >
        <div className="flex flex-col justify-center text-left">
          <div className="font-semibold mb-2 flex items-center"><img className='w-7 h-7 mr-3' src={circuit} alt="Prompt Icon" /><span className='text-md'>Customise Prompt</span></div>
          <p className="text-sm text-[#999999] text-left">
          Tailor your prompt using our templates and AI suggestions
          </p>
        </div>
      </div>

      <div
        className="w-[300px] h-[150px] flex flex-col justify-center items-center p-6 text-white bg-cover bg-center rounded-md shadow-lg"
      style={{ backgroundImage: `url(${cardbg})`, backgroundSize: "cover" }} 
      >
        <div className="flex flex-col justify-center text-left">
          <div className="font-semibold mb-2 flex items-center"><img className='w-7 h-7 mr-3' src={circuit} alt="Prompt Icon" /><span className='text-md'>Generate & Refine</span></div>
          <p className="text-sm text-[#999999] text-left">
          Generate content, review, and fine-tune for the best results
          </p>
        </div>
      </div>
    </div>
    </div>
  )
}

export default HowItWorks