import React from 'react';
import cardbg from '../../assets/howitworkscard.png';
import circuit from '../../assets/circuit.png';
import mask from '../../assets/Mask.png';

const HowItWorks = () => {
  // Define an array of objects for card content
  const steps = [
    {
      id: 1,
      title: 'Choose your AI platform',
      description: 'Choose your desired AI platform (e.g., GPT, DALL-E)',
      icon: circuit, // Reference to your image asset
    },
    {
      id: 2,
      title: 'Customise Prompt',
      description: 'Tailor your prompt using our templates and AI suggestions',
      icon: circuit,
    },
    {
      id: 3,
      title: 'Generate & Refine',
      description: 'Generate content, review, and fine-tune for the best results',
      icon: circuit,
    },
  ];

  return (
    <div
      className=""
      style={{
        backgroundImage: `url(${mask})`,
        backgroundRepeat: 'no-repeat',
        backgroundSize: 'cover',
      }}
    >
      <h3 className="bg-gradient-to-r from-[#DADADA] to-[#999999] bg-clip-text text-transparent text-3xl sm:text-4xl p-8 sm:p-12 font-[Amenti] flex justify-center">
        How It Works
      </h3>

      <div className="flex flex-col sm:flex-row justify-center items-center gap-2 sm:gap-10 pb-16">
        {steps.map((step) => (
          <div
            key={step.id}
            className="w-[300px] h-[150px] flex flex-col justify-center items-center p-6 text-white bg-cover bg-center rounded-md shadow-lg"
            style={{
              backgroundImage: `url(${cardbg})`,
              backgroundSize: 'contain',
              backgroundRepeat: 'no-repeat',
            }}
          >
            <div className="flex flex-col justify-center text-left">
              <div className="font-semibold mb-2 flex items-center">
                <img className="w-7 h-7 mr-3" src={step.icon} alt="Step Icon" />
                <span className="text-md">{step.title}</span>
              </div>
              <p className="text-sm text-[#999999] text-left">{step.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default HowItWorks;
