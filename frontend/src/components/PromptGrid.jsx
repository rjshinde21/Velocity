import React, { useState } from "react";
import star from "../assets/Home/star.png";
import GetStartedBtn from "./GetStartedBtn";
import { CheckCheckIcon, Clipboard } from "lucide-react";

const PromptGrid = () => {
  const prompts = [
    "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
    "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
    "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
    "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
    "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
    "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
    "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
    "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
    "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
  ];

  const [copiedIndex, setCopiedIndex] = useState(null);

  const copyToClipboard = (text, index) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    });
  };

  return (
    <div className="p-8">
      <h2 className="text-[#999999] text-xl sm:text-2xl mb-5">Your Prompts</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-11">
        {prompts.map((prompt, index) => (
          <div
            key={index}
            className="border border-[#999999] rounded-2xl p-4 flex justify-between items-center"
          >
            <p className="text-white text-md font-[Inter]">{prompt}</p>
            <div className="p-4">
              {/* Clickable copy icon */}
              <span
                className="w-12 h-10 object-contain cursor-pointer text-[#2796ef]"
                alt="Copy"
                onClick={() => copyToClipboard(prompt, index)}
                title={copiedIndex === index ? "Copied!" : "Copy to Clipboard"}
              >{copiedIndex === index ? <CheckCheckIcon /> : <Clipboard />}</span>
            </div>
          </div>
        ))}
      </div>
      <button className="glowing-button flex items-center gap-2 sm:mt-12 mt-6">
            <span>Create More</span>
            <img src={star} alt="Star" />
        </button>
    </div>
  );
};

export default PromptGrid;
