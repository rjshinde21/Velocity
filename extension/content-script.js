// contentScript.js
// This script runs in the context of the web page
(function() {
let lastAuthState = null;

// Function to check auth state
function checkAuthState() {
        // Get token first
        const token = localStorage.getItem('token');
        console.log('Retrieved token:', token); // Debug log\
        console.log("Retrieved email" , localStorage.getItem('userEmail'))
    
  const authData = {    
    isAuthenticated: !!localStorage.getItem('token'),
    token: localStorage.getItem('token'),
    userId: localStorage.getItem('userId'),
    userName: localStorage.getItem('userName'),
    userEmail: localStorage.getItem('userEmail')
  };

  // Only send message if auth state has changed
  if (JSON.stringify(authData) !== JSON.stringify(lastAuthState) && ((!localStorage.getItem('token') && !localStorage.getItem('userEmail')) || 
  (localStorage.getItem('token') && localStorage.getItem('userEmail')))) {
    lastAuthState = authData;
    chrome.runtime.sendMessage({
      type: 'AUTH_CHANGED',
      data: authData
    });
  }
}

// Check auth state periodically
//setInterval(checkAuthState, 1000);

// Listen for storage changes
window.addEventListener('storage', (e) => {
  if (e.key?.startsWith('shared') || e.key === 'userId' || e.key === 'userName' || e.key === 'userEmail' || e.key === 'token') {
    checkAuthState();
  }
});

  // Check if script has already been initialized
  if (window.hasOwnProperty('velocityState')) {
    return; // Exit if already initialized
  }
  // Create state in window scope so it's accessible but won't be redeclared
  window.velocityState = {
    isEnabled: false,
    isInitialized: false,
    platform: 'General',
    styleType: 'professional',
    enhancedPrompts: [],
    lastResponse: null,
    platformSelectors: {
      chatgpt: '#prompt-textarea',
      claude: '.claude-textarea, div[contenteditable="true"]',
      gemini: 'textarea[dir="auto"]',
      general: 'textarea, div[contenteditable="true"]'
    },
    styleTransformations: {
      descriptive: {
        instruction: "Expand this into a detailed, vivid description",
        modifier: (text) => `Create a detailed and descriptive version of: ${text}`
      },
      creative: {
        instruction: "Transform this into a creative and unique perspective",
        modifier: (text) => `Generate a creative and innovative version of: ${text}`
      },
      professional: {
        instruction: "Make this more formal and business-appropriate",
        modifier: (text) => `Develop a professional and polished version of: ${text}`
      },
      concise: {
        instruction: "Make this more concise while maintaining clarity",
        modifier: (text) => `Create a concise and clear version of: ${text}`
      }
    }
  };
  function getState() {
    return window.velocityState;
  }
  // Create styles only once
  if (!document.querySelector('#velocity-styles')) {
    const styles = document.createElement('style');
    styles.id = 'velocity-styles';
    styles.textContent = `
      /* CSS Reset for our wrapper */
      .velocity-wrapper {
        position: relative !important;
        display: inline-block !important;
        width: 100% !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
        background: none !important;
        font: inherit !important;
        vertical-align: baseline !important;
      }
    
      /* Ensure wrapper doesn't affect the textarea/input styling */
      .velocity-wrapper textarea,
      .velocity-wrapper [contenteditable="true"] {
        width: 100% !important;
        margin: 0 !important;
        padding-right: 50px !important;
        box-sizing: border-box !important;
        position: relative !important;
        display: block !important;
        /* Preserve original styles */
        background: inherit !important;
        color: inherit !important;
        font: inherit !important;
        line-height: inherit !important;
        border: inherit !important;
        border-radius: inherit !important;
      }
    
      /* Button styles with increased specificity */
      .velocity-wrapper > .velocity-enhance-button {
        position: absolute !important;
        top: 50% !important;
        right: 12px !important;
        transform: translateY(-50%) !important;
        width: 32px !important;
        height: 32px !important;
        min-width: 32px !important;
        min-height: 32px !important;
        padding: 6px !important;
        margin: 0 !important;
        background: transparent !important;
        color: white !important;
        border: 1px solid #444444 !important;
        border-radius: 6px !important;
        cursor: pointer !important;
        z-index: 999999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        opacity: 0 !important;
        transition: all 0.2s ease !important;
        pointer-events: none !important;
        box-shadow: none !important;
        font-size: initial !important;
        line-height: initial !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        word-spacing: normal !important;
        box-sizing: border-box !important;
      }
    
      .velocity-wrapper > .velocity-enhance-button:hover {
        background: black !important;
        box-shadow: 0 2px 8px rgba(0, 138, 203, 0.3) !important;
        transform: translateY(-50%) scale(1.05) !important;
      }
    
      .velocity-wrapper > .velocity-enhance-button.visible {
        opacity: 1 !important;
        pointer-events: auto !important;
      }
    
      .velocity-wrapper > .velocity-enhance-button:disabled.visible {
        opacity: 0.5 !important;
        cursor: not-allowed !important;
        transform: translateY(-50%) scale(1) !important;
        pointer-events: none !important;
      }
    
      .velocity-wrapper > .velocity-enhance-button img {
        width: 35px !important;
        height: 35px !important;
        transition: transform 0.2s ease !important;
        object-fit: contain !important;
        margin: 0 !important;
        padding: 0 !important;
        display: block !important;
        border: none !important;
        background: none !important;
      }
    
      .velocity-wrapper > .velocity-enhance-button:hover:not(:disabled) img {
        transform: scale(1.1) !important;
      }
    `;
          document.head.appendChild(styles);
  }
  // Helper function to update button visibility
  function updateButtonVisibility() {
    document.querySelectorAll('.velocity-enhance-button').forEach(button => {
      if (window.velocityState.isEnabled) {
        button.classList.add('visible');
        if (!button.disabled) {
          button.style.pointerEvents = 'auto';
        }
      } else {
        button.classList.remove('visible');
        button.style.pointerEvents = 'none';
      }
    });
  }
  
  // Function to handle prompt enhancement
  async function enhancePrompt(originalText) {
    try {
      const state = getState();
      const styleTransform = state.styleTransformations[state.styleType.toLowerCase()];
      if (!styleTransform) {
        throw new Error('Invalid style type selected');
      }
      const modifiedPrompt = styleTransform.modifier(originalText);
      const response = await fetch('http://localhost:2000/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `data=${encodeURIComponent(JSON.stringify({
          prompt: modifiedPrompt,
          style: state.styleType,
          AIType: state.platform,
          singlePrompt: true
        }))}`
      });
      const data = await response.json();
      const enhancedPrompt = JSON.parse(data.response).prompts[0].prompt;
      return enhancedPrompt;
    } catch (error) {
      console.error('Enhancement failed:', error);
      throw error;
    }
  }
  // Function to create and attach enhance button
  function createEnhanceButton(inputElement) {
    // Double-check that we don't already have a button
    if (inputElement.dataset.hasEnhanceButton === 'true' || 
        inputElement.closest('.velocity-wrapper') ||
        inputElement.parentElement?.querySelector('.velocity-enhance-button')) {
      return;
    }
  
    // Create wrapper with proper positioning
    const wrapper = document.createElement('div');
    wrapper.className = 'velocity-wrapper';
    
    // Mark the input as enhanced before doing anything else
    inputElement.dataset.hasEnhanceButton = 'true';
    
    // Position the wrapper correctly relative to the input
    const inputStyles = window.getComputedStyle(inputElement);
    wrapper.style.width = inputStyles.width;
    wrapper.style.height = inputStyles.height;
    
    // Create button with PNG image
    const button = document.createElement('button');
    button.className = 'velocity-enhance-button';
    
    // Create and set up the image element
    const img = document.createElement('img');
    img.src = chrome.runtime.getURL('assets/logo.png');
    img.alt = 'Enhance';
    img.draggable = false;
    button.appendChild(img);
    button.title = 'Enhance text';
  
    // Add loading state handling
    const showLoading = () => {
      button.disabled = true;
      button.style.pointerEvents = 'none';
      img.src = chrome.runtime.getURL('assets/logo.png');
      img.classList.add('animate-spin');
    };
    
    const hideLoading = () => {
      button.disabled = false;
      if (window.velocityState.isEnabled) {
        button.style.pointerEvents = 'auto';
      }
      img.src = chrome.runtime.getURL('assets/logo.png');
      img.classList.remove('animate-spin');
    };
    
    // Set up the click handler
    button.addEventListener('click', async () => {
      const text = inputElement.value || inputElement.textContent;
      if (!text) return;
      try {
        showLoading();
        const enhancedText = await enhancePrompt(text);
        if (inputElement.value !== undefined) {
          inputElement.value = enhancedText;
        } else {
          inputElement.textContent = enhancedText;
        }
        inputElement.dispatchEvent(new Event('input', { bubbles: true }));
      } catch (error) {
        console.error('Enhancement failed:', error);
        button.style.background = 'linear-gradient(180deg, #FF4444 0%, #CC0000 100%)';
        setTimeout(() => {
          button.style.background = '';
        }, 1000);
      } finally {
        hideLoading();
      }
    });
   // Set up proper DOM structure
   if (!inputElement.closest('.velocity-wrapper')) {
    inputElement.parentNode.insertBefore(wrapper, inputElement);
    wrapper.appendChild(inputElement);
    wrapper.appendChild(button);
  }

  // Add visibility based on state
  if (getState().isEnabled) {
    button.classList.add('visible');
  }

  // Adjust wrapper dimensions on input resize
  const resizeObserver = new ResizeObserver(() => {
    const styles = window.getComputedStyle(inputElement);
    wrapper.style.width = styles.width;
    wrapper.style.height = styles.height;
  });
  resizeObserver.observe(inputElement);
}
 function findAndEnhanceInputs() {
  const state = getState();
  const selector = state.platformSelectors[state.platform.toLowerCase()] ||
                  state.platformSelectors.general;
                  
  document.querySelectorAll(selector).forEach(input => {
    // Check if input is already wrapped or has a button
    if (input.closest('.velocity-wrapper') || 
        input.dataset.hasEnhanceButton === 'true' || 
        input.parentElement?.querySelector('.velocity-enhance-button')) {
      return; // Skip if already enhanced
    }
    
    // Check if input is actually visible and interactive
    const style = window.getComputedStyle(input);
    if (style.display === 'none' || style.visibility === 'hidden' || 
        input.offsetParent === null || input.disabled) {
      return; // Skip hidden or disabled inputs
    }
    
    createEnhanceButton(input);
  });
}
function cleanupEnhanceButtons() {
  document.querySelectorAll('.velocity-wrapper').forEach(wrapper => {
    const input = wrapper.querySelector('textarea, [contenteditable="true"]');
    const parent = wrapper.parentNode;
    if (input) {
      input.dataset.hasEnhanceButton = 'false';
      parent.insertBefore(input, wrapper);
      wrapper.remove();
    }
  });
}

// Message handler to update parameters from extension
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  try {
    if (message.action === 'updateEnhanceParameters') {
      const state = getState();
      
      // If being disabled, clean up existing buttons
      if (!message.enabled && state.isEnabled) {
        cleanupEnhanceButtons();
      }
      
      // Update parameters in state
      state.platform = message.platform;
      state.styleType = message.style;
      state.isEnabled = message.enabled;
      
      // Only find and enhance inputs if enabled
      if (state.isEnabled) {
        findAndEnhanceInputs();
        updateButtonVisibility();
      }
      
      return true;
    }
  } catch (error) {
    console.error('Error handling message:', error);
  }
  return false;
});

  // Initial setup
  findAndEnhanceInputs();
})();
