import React from 'react';

const HowItWorks = () => {
  const steps = [
    {
      icon: (
        <img
          src="https://toteminteractive.in/velosty/work1.png"
          alt="Step 1 Icon"
          className="w-5 h-5"
        />
      ),
      title: "Choose your AI platform",
      description: "Choose your desired AI platform (e.g., GPT, DALL-E)",
    },
    {
      icon: (
        <img
          src="https://toteminteractive.in/velosty/work2.png"
          alt="Step 2 Icon"
          className="w-5 h-5"
        />
      ),
      title: "Customise Prompt",
      description: "Tailor your prompt using our templates and AI suggestions",
    },
    {
      icon: (
        <img
          src="https://toteminteractive.in/velosty/work3.png"
          alt="Step 3 Icon"
          className="w-5 h-5"
        />
      ),
      title: "Generate & Refine",
      description: "Generate content, review, and fine tune for the best results",
    },
  ];

  return (
    <div className="relative w-full min-h-screen bg-black text-white p-8">
      {/* Background Image Layer */}
      <div
        className="absolute inset-0 bg-center bg-cover opacity-50 pt-12"
        style={{
          backgroundImage: "url('https://toteminteractive.in/velosty/mask.png')",
        }}
      ></div>
      <div className="relative max-w-7xl mx-auto">
        {/* Heading */}
        <h1 className="text-4xl font-light mt-12 ml-24 text-left">How It Works</h1>

        <div className="flex flex-col lg:flex-row gap-20">
          {/* Left side - Steps */}
          <div className="flex p-6 flex-col justify-center items-center space-y-2 lg:w-2/5">
            {steps.map((step, index) => (
              <div
                key={index}
                className="flex flex-col w-2/3 p-6 rounded-lg bg-[rgba(0,0,0,0.3)] border border-gray-800 backdrop-blur-sm transition-transform hover:transform hover:-translate-y-1"
              >
                <div className="flex flex-row items-center space-x-2">
                  <div className="flex-shrink-0 p-2 bg-[rgba(0,128,203,0.1)] rounded-lg">
                    {step.icon}
                  </div>
                  <h3 className="text-base font-medium text-white">
                    {step.title}
                  </h3>
                </div>

                <p className="text-xs text-gray-400 mt-2 ml-2">
                  {step.description}
                </p>
              </div>
            ))}
          </div>

          {/* Right side - Video Placeholder */}
          <div className="lg:w-2/5">
            <div
              className="relative rounded-lg overflow-hidden bg-gradient-to-br from-gray-900 to-gray-800"
              style={{ aspectRatio: '514/588' }}
            >
              <video
                src="https://toteminteractive.in/velosty/Extension.mp4"
                className="w-full h-full object-cover"
                autoPlay
                loop
                muted
                controls
              />
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

export default HowItWorks;
