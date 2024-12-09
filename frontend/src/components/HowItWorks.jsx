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
    <div className="relative min-h-screen bg-black">
      {/* Background Image Container */}
      <div
        className="absolute inset-0 bg-center bg-cover opacity-50"
        style={{
          backgroundImage: "url('https://toteminteractive.in/velosty/mask.png')",
        }}
      />

      {/* Content Container */}
      <div className="relative w-full px-4 sm:px-6 lg:px-8 py-14">
        <div className="max-w-7xl mx-auto flex flex-col lg:flex-row gap-8">
          {/* Left Section */}
          <div className="w-full lg:w-1/2 px-4">
            <h1 className="font-[Amenti] text-3xl sm:text-4xl font-light mb-8 text-white text-center lg:text-left lg:ml-20">
              How It Works
            </h1>
            <div className="flex flex-col items-center space-y-4 w-full lg:w-3/4 pt-10">
              {steps.map((step, index) => (
                <div
                  key={index}
                  className="flex flex-col w-full sm:w-4/5 lg:w-2/3 p-4 sm:p-6 rounded-2xl bg-[rgba(0,0,0,0.3)] border border-gray-800 backdrop-blur-sm transition-transform transform hover:translate-y-2"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="bg-[rgba(0,128,203,0.1)] p-2 rounded-lg">
                      {step.icon}
                    </div>
                    <h3 className="text-base sm:text-lg text-white">{step.title}</h3>
                  </div>
                  <p className="text-gray-400 text-xs sm:text-sm ml-4 sm:ml-8">
                    {step.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Right side - Video Placeholder */}
          <div className="lg:w-1/2 items-start">
            <div
              className="relative rounded-lg overflow-hidden bg-gradient-to-br from-gray-900 to-gray-800 h-4/5"
              style={{ aspectRatio: '677/766' }}
            >
              <video
                src="https://toteminteractive.in/velosty/Extensionnew.mp4"
                className="w-full h-full object-cover pointer-events-none"
                autoPlay
                loop
                muted
                playsInline
                disablePictureInPicture
                controlsList="nodownload noplaybackrate"
                preload="auto"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HowItWorks;