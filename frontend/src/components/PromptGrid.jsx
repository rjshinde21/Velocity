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
  const [expandedPrompts, setExpandedPrompts] = useState(new Set());

  const userId = localStorage.getItem('userId');
  const authToken = localStorage.getItem('token');

  useEffect(() => {
    fetchPromptHistory();
  }, []);

  const fetchPromptHistory = async () => {
    try {
      setLoading(true);
      const response = await fetch(`https://thinkvelocity.in/api/api/history/user/history?user_id=${userId}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch prompt history');
      }

      const data = await response.json();
      const processedPrompts = organizePrompts(data.data || []);
      setPrompts(processedPrompts);
    } catch (err) {
      console.error('Error fetching prompt history:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Organizing prompts function remains the same
  const organizePrompts = (rawPrompts) => {
    const processedPrompts = [];
    const inputPrompts = new Map();

    rawPrompts.forEach(prompt => {
      if (prompt.content_type === 'input_prompt') {
        inputPrompts.set(prompt.history_id, prompt);
      }
    });

    rawPrompts.forEach(prompt => {
      if (prompt.content_type === 'copied_response' && prompt.original_prompt_id) {
        const originalPrompt = inputPrompts.get(prompt.original_prompt_id);
        if (originalPrompt) {
          processedPrompts.push({
            type: 'paired',
            prompt: originalPrompt,
            response: prompt
          });
        }
      }
    });

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

    return processedPrompts.sort((a, b) => {
      const dateA = a.response ? new Date(a.response.created_at) : new Date(a.prompt.created_at);
      const dateB = b.response ? new Date(b.response.created_at) : new Date(b.prompt.created_at);
      return dateB - dateA;
    });
  };

  const copyToClipboard = (text, index, e) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text).then(() => {
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    });
  };

  const handleLoadMore = () => {
    setVisiblePrompts(prev => Math.min(prev + 4, prompts.length));
  };

  const toggleExpand = (id) => {
    setExpandedPrompts(prev => {
      const updated = new Set(prev);
      if (updated.has(id)) {
        updated.delete(id);
      } else {
        updated.add(id);
      }
      return updated;
    });
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

      <div className="h-[calc(100vh-200px)] overflow-hidden"> {/* Adjust 200px based on your header/footer height */}
        <div className="h-full overflow-y-auto px-1 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5 lg:gap-6 mb-6 sm:mb-11 auto-rows-auto">
            {prompts.slice(0, visiblePrompts).map((item, index) => (
              <div
                key={item.prompt.history_id}
                className={`border border-[#999999] rounded-2xl p-4 sm:p-5 lg:p-6
              flex flex-col gap-3
              transition-all duration-300 hover:border-[#2796ef]
              bg-black/5 backdrop-blur-sm
              ${expandedPrompts.has(item.prompt.history_id) ? 'cursor-pointer' : 'min-h-[160px] cursor-pointer'}`}
              >
                <div className="flex flex-col h-full" onClick={() => toggleExpand(item.prompt.history_id)}>
                  {item.response ? (
                    <>
                      <p className={`text-[#999999] text-xs sm:text-sm font-[Inter] mb-2
                    ${expandedPrompts.has(item.prompt.history_id) ? '' : 'line-clamp-2'}`}>
                        {item.prompt.prompt_text}
                      </p>
                      <div className="flex justify-between items-start gap-3 flex-grow">
                        <p className={`text-[#999999] text-lg sm:text-xl lg:text-2xl font-[Inter]
                      ${expandedPrompts.has(item.prompt.history_id) ? '' : 'line-clamp-4'}`}>
                          {item.response.prompt_text}
                        </p>
                        <img
                          className="w-6 h-6 cursor-pointer text-[#2796ef] flex-shrink-0
                        hover:scale-105 transition-transform duration-200"
                          src={copiedIndex === index ? copied : copy}
                          alt="Copy"
                          onClick={(e) => {
                            e.stopPropagation();
                            copyToClipboard(item.response.prompt_text, index, e);
                          }}
                          title={copiedIndex === index ? "Copied!" : "Copy to Clipboard"}
                        />
                      </div>
                    </>
                  ) : (
                    <div className="flex justify-between items-start gap-3 flex-grow">
                      <p className={`text-[#999999] text-lg sm:text-xl lg:text-2xl font-[Inter]
                    ${expandedPrompts.has(item.prompt.history_id) ? '' : 'line-clamp-6'}`}>
                        {item.prompt.prompt_text}
                      </p>
                      <img
                        className="w-6 h-6 cursor-pointer text-[#2796ef] flex-shrink-0
                      hover:scale-105 transition-transform duration-200"
                        src={copiedIndex === index ? copied : copy}
                        alt="Copy"
                        onClick={(e) => {
                          e.stopPropagation();
                          copyToClipboard(item.prompt.prompt_text, index, e);
                        }}
                        title={copiedIndex === index ? "Copied!" : "Copy to Clipboard"}
                      />
                    </div>
                  )}
                </div>

                <div className="flex justify-between text-[#999999] text-xs mt-auto pt-2 border-t border-[#999999]/20">
                  <span>{item.prompt.ai_type}</span>
                  <span>{new Date(item.prompt.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {visiblePrompts < prompts.length && prompts.length > 0 && (
        <div className="w-full flex justify-center">
          <button
            onClick={handleLoadMore}
            className="flex justify-center text-lg px-6 py-2 text-[#ffffff] border border-[#444444] 
              transition-all duration-200 rounded-[35px] items-center bg-[#D9D9D966] 
              hover:bg-[#D9D9D999] hover:border-[#666666]"
          >
            Load more
            <ChevronDown className="ml-2" />
          </button>
        </div>
      )}

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