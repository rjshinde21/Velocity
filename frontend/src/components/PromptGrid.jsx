import React, { useState, useEffect } from "react";
import star from "../assets/Home/star.png";
import copy from "../assets/copy.png";
import copied from "../assets/copied.png";
import { ChevronDown } from 'lucide-react';

const PromptGrid = () => {
  const [prompts, setPrompts] = useState([]);
  const [visiblePrompts, setVisiblePrompts] = useState(4);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [createClicked, setCreateClicked] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const userId = localStorage.getItem('userId');
  const authToken = localStorage.getItem('token');
  useEffect(() => {
    fetchPromptHistory();
  }, []);

  const fetchPromptHistory = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://127.0.0.1:3000/api/history/user/history?user_id=${userId}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch prompt history');
      }

      const data = await response.json();
      console.log("API Response:", data); // Debug log
      
      // Process and organize prompts
      const processedPrompts = organizePrompts(data.data || []);
      console.log("Processed Prompts:", processedPrompts); // Debug log
      setPrompts(processedPrompts);
    } catch (err) {
      console.error('Error fetching prompt history:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Function to organize prompts and their responses
  const organizePrompts = (rawPrompts) => {
    const processedPrompts = [];
    const inputPrompts = new Map();

    // First pass: collect all input prompts
    rawPrompts.forEach(prompt => {
        if (prompt.content_type === 'input_prompt') {
            inputPrompts.set(prompt.history_id, prompt);
        }
    });

    // Second pass: create entries for each response, paired with its original prompt
    rawPrompts.forEach(prompt => {
        if (prompt.content_type === 'copied_response' && prompt.original_prompt_id) {
            const originalPrompt = inputPrompts.get(prompt.original_prompt_id);
            if (originalPrompt) {
                // Create a new card for each response
                processedPrompts.push({
                    type: 'paired',
                    prompt: originalPrompt,
                    response: prompt
                });
            }
        }
    });

    // Third pass: add prompts without responses
    inputPrompts.forEach(prompt => {
        const hasResponse = processedPrompts.some(
            p => p.prompt.history_id === prompt.history_id
        );
        if (!hasResponse) {
            processedPrompts.push({
                type: 'input_prompt',
                prompt: prompt,
                response: null
            });
        }
    });

    // Sort by creation date, newest first
    return processedPrompts.sort((a, b) => {
        // For paired prompts, use the response date for sorting
        const dateA = a.response ? new Date(a.response.created_at) : new Date(a.prompt.created_at);
        const dateB = b.response ? new Date(b.response.created_at) : new Date(b.prompt.created_at);
        return dateB - dateA;
    });
};


  const copyToClipboard = (text, index) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    });
  };

  const handleLoadMore = () => {
    setVisiblePrompts(prev => Math.min(prev + 4, prompts.length));
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h2 className="text-[#999999] text-xl sm:text-2xl mb-5">Your Prompts</h2>
      {prompts.length === 0 && (
        <p className="text-[#808080] text-sm sm:text-xl py-2 sm:py-4">
          You have no prompts as of now. Create now to get started!
        </p>
      )}
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6 sm:mb-11">
        {prompts.slice(0, visiblePrompts).map((item, index) => (
          <div
            key={item.prompt.history_id}
            className="border border-[#999999] rounded-2xl p-8 flex flex-col gap-4"
          >
            {/* If there's a response, show both prompt and response */}
            {item.response ? (
              <>
                <p className="text-[#999999] text-sm font-[Inter]">
                  {item.prompt.prompt_text}
                </p>
                <div className="flex justify-between items-start gap-4">
                  <p className="text-[#999999] text-[32px] font-[Inter]">
                    {item.response.prompt_text}
                  </p>
                  <img
                    className="w-30 h-10 cursor-pointer text-[#2796ef] flex-shrink-0"
                    src={copiedIndex === index ? copied : copy}
                    alt="Copy"
                    onClick={() => copyToClipboard(item.response.prompt_text, index)}
                    title={copiedIndex === index ? "Copied!" : "Copy to Clipboard"}
                  />
                </div>
              </>
            ) : (
              /* If there's no response, just show the prompt in large text */
              <div className="flex justify-between items-start gap-4">
                <p className="text-[#999999] text-[32px] font-[Inter]">
                  {item.prompt.prompt_text}
                </p>
                <img
                  className="w-30 h-10 cursor-pointer text-[#2796ef] flex-shrink-0"
                  src={copiedIndex === index ? copied : copy}
                  alt="Copy"
                  onClick={() => copyToClipboard(item.prompt.prompt_text, index)}
                  title={copiedIndex === index ? "Copied!" : "Copy to Clipboard"}
                />
              </div>
            )}

            {/* AI Type and Date */}
            <div className="flex justify-between text-[#999999] text-xs mt-2">
              <span>{item.prompt.ai_type}</span>
              <span>{new Date(item.prompt.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Load More Button */}
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

      {/* Create More Button */}
      <button
        onClick={() => setCreateClicked(prev => !prev)}
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