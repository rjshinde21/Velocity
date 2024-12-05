const state = {
  isEnabled: false,
  isInitialized: false,
  selectedLLM: 'General', // Default LLM type
  enhancedPrompts: [] // Store generated prompts
};
// Single style definition
const enhanceStyles = document.createElement('style');
enhanceStyles.textContent = `
  .velocity-enhance-button {
    position: absolute !important;
    bottom: 10px !important;
    right: 10px !important;
    padding: 6px 12px !important;
    background: linear-gradient(180deg, #000000 0%, #008ACB 100%) !important;
    color: white !important;
    border: 1px solid #444444 !important;
    border-radius: 5px !important;
    cursor: pointer !important;
    z-index: 999999 !important;
    display: none !important;
  }

  .velocity-enhance-button.visible {
    display: block !important;
  }

  .velocity-wrapper {
    position: relative !important;
    display: inline-block !important;
    width: 100% !important;
  }

  .velocity-prompt-popup {
    position: absolute !important;
    bottom: calc(100% + 10px) !important;
    left: 0 !important;
    width: 300px !important;
    max-height: 400px !important;
    background: #000000 !important;
    border: 1px solid #444444 !important;
    border-radius: 8px !important;
    padding: 12px !important;
    z-index: 999999 !important;
    display: none;
    overflow-y: auto !important;
    color: white !important;
  }

  .velocity-prompt-option {
    padding: 12px !important;
    margin-bottom: 8px !important;
    background: rgba(0, 138, 203, 0.1) !important;
    border: 1px solid #444444 !important;
    border-radius: 6px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
  }

  .velocity-prompt-option:hover {
    background: rgba(0, 138, 203, 0.2) !important;
    transform: translateY(-1px) !important;
  }

  .velocity-prompt-actions {
    display: flex !important;
    gap: 8px !important;
    margin-top: 8px !important;
  }

  .velocity-prompt-button {
    flex: 1 !important;
    padding: 6px 12px !important;
    background: linear-gradient(180deg, #008ACB 0%, #006494 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 4px !important;
    cursor: pointer !important;
    font-size: 12px !important;
  }
`;
document.head.appendChild(enhanceStyles);

// Single function to handle button visibility
function updateButtonVisibility() {
  document.querySelectorAll('.velocity-enhance-button').forEach(button => {
    if (state.isEnabled) {
      button.classList.add('visible');
    } else {
      button.classList.remove('visible');
    }
  });
}

// Single function to enhance inputs
async function generateEnhancedPrompts(text) {
  try {
    const response = await fetch('http://localhost:2000/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `data=${encodeURIComponent(JSON.stringify({
        prompt: text,
        style: 'professional',
        AIType: state.selectedLLM
      }))}`
    });

    const data = await response.json();
    return JSON.parse(data.response).prompts;
  } catch (error) {
    console.error('Failed to generate prompts:', error);
    throw error;
  }
}

// Enhanced input enhancement function
function enhanceInput(input) {
  if (input.dataset.velocityEnhanced) return;
  
  const wrapper = document.createElement('div');
  wrapper.className = 'velocity-wrapper';
  input.parentNode.insertBefore(wrapper, input);
  wrapper.appendChild(input);

  const button = document.createElement('button');
  button.textContent = 'Enhance';
  button.className = 'velocity-enhance-button';
  if (state.isEnabled) {
    button.classList.add('visible');
  }

  // Create popup for enhanced prompts
  const promptPopup = document.createElement('div');
  promptPopup.className = 'velocity-prompt-popup';
  wrapper.appendChild(promptPopup);

  button.addEventListener('click', async () => {
    const text = input.value || input.textContent;
    if (!text) return;

    try {
      button.disabled = true;
      button.textContent = 'Enhancing...';
      promptPopup.style.display = 'block';

      // Show loading state
      promptPopup.innerHTML = `
        <div class="velocity-prompt-option">
          Generating enhanced prompts...
        </div>
      `;

      // Generate prompts
      const prompts = await generateEnhancedPrompts(text);
      state.enhancedPrompts = prompts;

      // Show prompts with actions
      promptPopup.innerHTML = prompts.map((prompt, index) => `
        <div class="velocity-prompt-option">
          ${prompt.prompt}
          <div class="velocity-prompt-actions">
            <button class="velocity-prompt-button" onclick="window.velocityActions.copyPrompt(${index})">
              Copy
            </button>
            <button class="velocity-prompt-button" onclick="window.velocityActions.replacePrompt(${index})">
              Replace
            </button>
          </div>
        </div>
      `).join('');

    } catch (error) {
      console.error('Enhancement failed:', error);
      promptPopup.innerHTML = `
        <div class="velocity-prompt-option">
          Failed to generate prompts. Please try again.
        </div>
      `;
    } finally {
      button.disabled = false;
      button.textContent = 'Enhance';
    }
  });

  // Add popup close handler
  document.addEventListener('click', (e) => {
    if (!promptPopup.contains(e.target) && !button.contains(e.target)) {
      promptPopup.style.display = 'none';
    }
  });

  wrapper.appendChild(button);
  input.dataset.velocityEnhanced = 'true';

  // Add global actions for the buttons
  window.velocityActions = {
    copyPrompt: (index) => {
      const prompt = state.enhancedPrompts[index].prompt;
      navigator.clipboard.writeText(prompt);
      promptPopup.style.display = 'none';
    },
    replacePrompt: (index) => {
      const prompt = state.enhancedPrompts[index].prompt;
      if (input.value !== undefined) {
        input.value = prompt;
      } else {
        input.textContent = prompt;
      }
      input.dispatchEvent(new Event('input', { bubbles: true }));
      promptPopup.style.display = 'none';
    }
  };
}

// Single function to scan for inputs
function findAndEnhanceInputs() {
  const inputs = document.querySelectorAll(`
    textarea,
    div[contenteditable="true"],
    .claude-input-area textarea,
    #prompt-textarea,
    [role="textbox"]
  `);

  inputs.forEach(input => {
    if (!input.closest('.velocity-wrapper')) {
      enhanceInput(input);
    }
  });
}

// Single observer instance
const observer = new MutationObserver(() => {
  if (state.isEnabled) {
    findAndEnhanceInputs();
  }
});

// Message handler
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'toggleEnhanceButton') {
    state.isEnabled = message.enabled;
    updateButtonVisibility();
    
    if (!state.isInitialized) {
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
      state.isInitialized = true;
    }
  } else if (message.action === 'setLLMType') {
    state.selectedLLM = message.llmType;
  }
});

// Initial setup
findAndEnhanceInputs();