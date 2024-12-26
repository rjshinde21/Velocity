import React from 'react';
import cardbg from "../assets/howitworkscard.png";

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
    <div className="relative bg-black">
      {/* Background Image Container */}
      <div
        className="absolute inset-0 bg-center bg-cover opacity-50"
        style={{ backgroundImage: "url('https://toteminteractive.in/velosty/mask.png')" }}
      />

      {/* Content Container */}
      <div className="relative w-full px-4 sm:px-6 lg:px-6 py-16 sm:py-20">
        <div className="max-w-[1440px] mx-auto flex flex-col lg:flex-row lg:justify-between gap-6">


          {/* Left Section */}
          <div className="w-full lg:w-1/2 px-4 flex flex-col justify-start">
            <h1 className="font-Amenti text-3xl sm:text-4xl font-light text-white text-center lg:text-left lg:ml-20">
              How It Works
            </h1>

            {/* Mobile Video - Shows first on mobile, hidden on desktop */}
            <div className="lg:hidden w-full">
              <div className="w-full max-w-2xl mx-auto pt-4">
                <div className="relative rounded-lg overflow-hidden bg-transparent aspect-[1578/1080]">
                  <video
                    src="https://toteminteractive.in/velosty/Demo%20Draft%209_2_prob3.webm"
                    className="absolute inset-0 w-full h-full object-cover pointer-events-none select-none"
                    autoPlay
                    loop
                    muted
                    playsInline
                    disablePictureInPicture
                    controlsList="nodownload nofullscreen noremoteplayback"
                    controls={false}
                  />
                  <div className="absolute inset-0 z-10" aria-hidden="true" />
                </div>
              </div>
            </div>
            <div className="flex flex-col items-center space-y-4 w-full lg:w-3/4 pt-8">
              {steps.map((step, index) => (
                <div
                  key={index}
                  className="flex flex-col w-full sm:w-4/5 lg:w-full min-h-[120px] p-4 sm:p-6 rounded-2xl bg-[rgba(0,0,0,0.3)] border border-gray-800 backdrop-blur-sm transition-transform transform hover:translate-y-2"
                  style={{
                    backgroundImage: `url(${cardbg})`,
                    backgroundSize: "100% 100%",
                    backgroundRepeat: "no-repeat",
                  }}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="bg-[rgba(0,128,203,0.1)] p-2 rounded-lg">
                      {step.icon}
                    </div>
                    <h3 className="text-base sm:text-lg text-white">{step.title}</h3>
                  </div>
                  <p className="text-gray-400 text-xs sm:text-sm ml-4 sm:ml-8 flex-grow">
                    {step.description}
                  </p>
                </div>
              ))}
            </div>

          </div>

          {/* Desktop Video - Hidden on mobile, shows on desktop */}
          <div className="hidden lg:flex w-full lg:w-full mb-4 items-center justify-center px-8 ">
    <div className="w-full max-w-5xl">
        <div className="relative rounded-lg overflow-hidden bg-transparent aspect-[1600/1080] w-full">
            <video
                src="https://toteminteractive.in/velosty/Demo%20Draft%209_2_prob3.webm"
                className="absolute inset-0 w-full h-full object-contain pointer-events-none select-none"
                autoPlay
                loop
                muted
                playsInline
                disablePictureInPicture
                controlsList="nodownload nofullscreen noremoteplayback"
                controls={false}
            />
            <div className="absolute inset-0 z-10" aria-hidden="true" />
        </div>
    </div>
</div>
        </div>
      </div>
    </div>
  );
};

export default HowItWorks;