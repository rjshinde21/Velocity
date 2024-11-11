import React from 'react'
import HowItWorksCard from './HowItWorksCard'

const HowItWorks = () => {
  return (
    <div>
        <h3 className="bg-gradient-to-r from-[#DADADA] to-[#999999] bg-clip-text text-transparent text-3xl sm:text-4xl p-4 sm:p-10 font-[Amenti]">Explore our Plans</h3>
        <div className="flex flex-col sm:flex-row gap-4 sm:gap-8">
        <HowItWorksCard />
        <HowItWorksCard />
        <HowItWorksCard />
      </div>
    </div>
  )
}

export default HowItWorks