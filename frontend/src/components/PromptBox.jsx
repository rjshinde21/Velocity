import React, { useState } from 'react';

const PromptBox = () => {
  const [prompt, setPrompt] = useState('');
  const [selectedStyle, setSelectedStyle] = useState('');
  const [selectedAI, setSelectedAI] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState('');

  const styles = [
    { id: 'descriptive', name: 'Descriptive', description: 'Detailed and vivid' },
    { id: 'creative', name: 'Creative', description: 'Unique and imaginative' },
    { id: 'professional', name: 'Professional', description: 'Formal and polished' },
    { id: 'concise', name: 'Concise', description: 'Clear and brief' }
  ];

  const aiTypes = [
    { id: 'chatgpt', name: 'ChatGPT' },
    { id: 'claude', name: 'Claude' },
    { id: 'midjourney', name: 'Midjourney' }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await fetch('https://thinkvelocity.in/python-api/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          prompt,
          style: selectedStyle,
          AIType: selectedAI,
          singlePrompt: true
        })
      });

      const data = await response.json();
      setResponse(data.enhanced_prompts?.[0]?.prompt || '');
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative z-20 max-w-4xl mx-auto px-4 py-8 pointer-events-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="pointer-events-auto">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter your prompt here..."
            className="w-full h-32 bg-[#121212] border border-[#1E1E1E] rounded-xl p-4 text-white 
              placeholder:text-gray-500 focus:outline-none focus:border-[#008ACB] resize-none"
          />
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pointer-events-auto">
          {styles.map((style) => (
            <button
              key={style.id}
              type="button"
              onClick={() => setSelectedStyle(style.id)}
              className={`p-4 rounded-xl border transition-all ${
                selectedStyle === style.id
                  ? 'border-[#008ACB] bg-[#008ACB]/10'
                  : 'border-[#1E1E1E] hover:border-[#008ACB]/50'
              }`}
            >
              <h3 className="text-white font-medium mb-1">{style.name}</h3>
              <p className="text-gray-400 text-sm">{style.description}</p>
            </button>
          ))}
        </div>

        <div className="flex flex-wrap gap-4 pointer-events-auto">
          {aiTypes.map((ai) => (
            <button
              key={ai.id}
              type="button"
              onClick={() => setSelectedAI(ai.id)}
              className={`px-6 py-3 rounded-lg border transition-all ${
                selectedAI === ai.id
                  ? 'border-[#008ACB] bg-[#008ACB]/10 text-white'
                  : 'border-[#1E1E1E] text-gray-400 hover:border-[#008ACB]/50'
              }`}
            >
              {ai.name}
            </button>
          ))}
        </div>

        <button
          type="submit"
          disabled={!prompt || !selectedStyle || !selectedAI || isLoading}
          className="w-full flex justify-center items-center bg-[#008ACB] text-white rounded-xl 
            py-4 font-medium transition-all hover:bg-[#0099E6] disabled:opacity-50 
            disabled:cursor-not-allowed pointer-events-auto"
        >
          {isLoading ? 'Generating...' : 'Generate Enhanced Prompt'}
        </button>
      </form>

      {response && (
        <div className="mt-8 p-6 bg-[#121212] border border-[#1E1E1E] rounded-xl pointer-events-auto">
          <h3 className="text-white font-medium mb-2">Enhanced Prompt:</h3>
          <p className="text-gray-300 whitespace-pre-wrap">{response}</p>
        </div>
      )}
    </div>
  );
};

export default PromptBox;