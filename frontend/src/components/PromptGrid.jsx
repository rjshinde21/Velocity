import React, { useState } from "react";
import star from "../assets/Home/star.png";
import copy from "../assets/copy.png";
import copied from "../assets/copied.png";
import { ChevronDown, Flag } from 'lucide-react';

const PromptGrid = () => {
  const prompts = [
    // "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
    // "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
    // "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
    // "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
    // "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
    // "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
    // "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
    // "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
    // "Qorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc vulputate libero et velit interdum, ac aliquet odio mattis.",
  ];

  const [visiblePrompts, setVisiblePrompts] = useState(4); 
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [createClicked, setCreateClicked] = useState(false)

  const copyToClipboard = (text, index) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    });
  };

  const handleLoadMore = () => {
    setVisiblePrompts(prompts.length); 
  };

  return (
    <div className="p-8">
      <h2 className="text-[#999999] text-xl sm:text-2xl mb-5">Your Prompts</h2>
      {prompts.length===0 && <p className="text-[#808080] text-sm sm:text-xl py-2 sm:py-4">You have no prompts as of now. Create now to get started!</p>}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6 sm:mb-11">
        {prompts.slice(0, visiblePrompts).map((prompt, index) => (
          <div
            key={index}
            className="border border-[#999999] rounded-2xl p-8 flex justify-between gap-4 items-center"
          >
            <p className="text-[#999999] text- sm:text-[32px] font-[Inter]">{prompt}</p>
      {/* Clickable copy icon */}
      <img
                className="w-30 h-10 cursor-pointer text-[#2796ef]"
                src={copiedIndex === index ? copied : copy}
                alt="Copy"
                onClick={() => copyToClipboard(prompt, index)}
                title={copiedIndex === index ? "Copied!" : "Copy to Clipboard"}
              />
          </div>
        ))}
      </div>

      {/* Show Load More button only if there are more prompts to load */}
      {visiblePrompts < prompts.length && prompts.length > 0 && (
        <div className="w-full flex justify-center">
          <button
            onClick={handleLoadMore}
            className="flex justify-center text-lg px-6 py-2 text-[#ffffff] border border-[#444444] transition-all duration-200 rounded-[35px] items-center bg-[#D9D9D966] hover:animate-icon-bounce"
          >
            Load more
            <span className="chevron-icon ml-2">
              <ChevronDown />
            </span>
          </button>
        </div>
      )}

      {/* Original Create More button */}
      <button
        onClick={() => setCreateClicked((prev) => !prev)}
        className="glowing-button w-full sm:w-auto flex justify-center items-center gap-2 sm:mt-12 mt-6 mb-4"
      >
        <span>Create{prompts.length > 0 ? " More" : ""}</span>
        <img src={star} alt="Star" />
      </button>
      {createClicked && (
        <span className="text-[#808080] text-md py-4">
          Please head towards the web store and download the extension!
        </span>
      )}
    </div>
  );
};

export default PromptGrid;
