// contentScript.js
// This script runs in the context of the web page
(function() {
let lastAuthState = null;
let lastSavedPromptId = null;  // Add this at the top with your other state variables
let lastTokensUsed = 0;

// Function to check auth state
  function checkAuthState() {
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
    chrome.storage.local.set({
      token: authData.token,
      userId: authData.userId,
      userName: authData.userName,
      userEmail: authData.userEmail
    });

    lastAuthState = authData;
    chrome.runtime.sendMessage({
      type: 'AUTH_CHANGED',
      data: authData
    });
  }
}
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'AUTH_STATE_CHANGED') {
    // Update localStorage only if the values are different
    const currentToken = localStorage.getItem('token');
    const currentEmail = localStorage.getItem('userEmail');
    
    if (message.data.token !== currentToken || message.data.userEmail !== currentEmail) {
      if (message.data.token) {
        localStorage.setItem('token', message.data.token);
        localStorage.setItem('userId', message.data.userId);
        localStorage.setItem('userName', message.data.userName);
        localStorage.setItem('userEmail', message.data.userEmail);
      } else {
        localStorage.removeItem('token');
        localStorage.removeItem('userId');
        localStorage.removeItem('userName');
        localStorage.removeItem('userEmail');
      }
    }
    lastAuthState = message.data;
  }
  if (message.action === 'toggleEnhanceButton') {
    if (window.velocityState) {
      window.velocityState.isEnabled = message.enabled;
      // Update UI or other state as needed
    }
  }
  if (message.action === 'updateEnhanceParameters') {
    (async () => {
      try {
        // First check authentication
        const storage = await chrome.storage.local.get(['token', 'isAuthenticated', 'userId']);
        const userId = storage.userId;
        const token = storage.token;
        if (!storage.isAuthenticated || !storage.token) {
          cleanupEnhanceButtons();
          sendResponse({
            success: false,
            error: 'Please log in to use this feature',
            type: 'auth'
          });
          return;
        }

        // Check tokens
        try {
          const response = await fetch(`http://127.0.0.1:3001/api/token-types/${userId}`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          const data = await response.json();
          
          if (data.data.token_received <= data.data.tokens_used) {
            cleanupEnhanceButtons();
            sendResponse({
              success: false,
              error: 'Insufficient tokens. Please purchase more tokens to continue.',
              type: 'tokens',
              remainingTokens: data.data.token_received - data.data.tokens_used
            });
            return;
          }
        } catch (error) {
          console.error('Error checking tokens:', error);
          sendResponse({
            success: false,
            error: 'Error checking token balance',
            type: 'error'
          });
          return;
        }

        // If all checks pass, proceed with the update
        console.log('Updating enhancement parameters:', message);
        const platformInfo = await detectPlatform();
        
        const currentState = window.velocityState || {};
        window.velocityState = {
          ...currentState,
          platformInfo: platformInfo,
          styleType: message.style,
          platform : message.platform,
          isEnabled: message.enabled && platformInfo.isSupported
        };

        if (window.velocityState.isEnabled && platformInfo.isSupported) {
          await findAndEnhanceInputs();
        } else {
          cleanupEnhanceButtons();
        }

        sendResponse({
          success: true,
          platformDetected: platformInfo.platform,
          isSupported: platformInfo.isSupported
        });
      } catch (error) {
        console.error('Error updating enhancement parameters:', error);
        sendResponse({ 
          success: false, 
          error: error.message,
          type: 'error'
        });
      }
    })();
    return true;
  }

});

// Check auth state periodically
setInterval(checkAuthState, 1000);

// Listen for storage changes
window.addEventListener('storage', (e) => {
  if (e.key?.startsWith('shared') || 
      e.key === 'userId' || 
      e.key === 'userName' || 
      e.key === 'userEmail' || 
      e.key === 'token') {
    checkAuthState();
  }
});
const PLATFORM_CONFIG = {
  chatgpt: {
    urlPattern: /^https:\/\/chatgpt\.com/,
    selectors: '#prompt-textarea',
    name: 'ChatGPT'
  },
  claude: {
    urlPattern: /^https:\/\/claude\.ai/,
    selectors: '.claude-textarea, div[contenteditable="true"]',
    name: 'Claude'
  },
  gemini: {
    urlPattern: /^https:\/\/gemini\.google\.com/,
    selectors: 'textarea[dir="auto"]',
    name: 'Gemini'
  },
  midjourney: {
    urlPattern: /^https:\/\/(www\.)?midjourney\.com|^https:\/\/(www\.)?discord\.com\/channels/,
    selectors: 'div[class*="messageInput"]',
    name: 'Midjourney'
  },
  canva: {
    urlPattern: /^https:\/\/(www\.)?canva\.com/,
    selectors: 'div[data-testid="text-editor"]',
    name: 'Canva'
  },
  stability: {
    urlPattern: /^https:\/\/(www\.)?stability\.ai/,
    selectors: 'textarea[placeholder*="prompt"], input[placeholder*="prompt"]',
    name: 'Stability AI'
  }
};

  // Check if script has already been initialized
  if (window.hasOwnProperty('velocityState')) {
    return; // Exit if already initialized
  }
  // Create state in window scope so it's accessible but won't be redeclared
  window.velocityState = {
    ...window.velocityState,
  platformSelectors: PLATFORM_CONFIG,
    isEnabled: false,
    isInitialized: false,
    platform: 'General',
    styleType: 'professional',
    enhancedPrompts: [],
    lastResponse: null,
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
  async function detectPlatform() {
    try {
      const url = window.location.href;
      console.log('Checking URL:', url);
      for (const [platform, config] of Object.entries(PLATFORM_CONFIG)) {
        if (config.urlPattern.test(url)) {
          console.log('Platform detected:', platform);
          return {
            isSupported: true,
            platform: platform,
            config: config
          };
        }
      }
      console.log('No supported platform detected');
      return {
        isSupported: false,
        platform: null,
        config: null
      };
    } catch (error) {
      console.error('Error in platform detection:', error);
      return {
        isSupported: false,
        platform: null,
        config: null
      };
    }
  }

  function getState() {
    return window.velocityState;
  }
  // Create styles only once
  if (!document.querySelector('#velocity-styles')) {
    const styles = document.createElement('style');
    styles.id = 'velocity-styles';
    styles.textContent = `
    .velocity-enhance-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: #666 !important;
}

.velocity-enhance-button:disabled:hover {
  transform: none !important;
  box-shadow: none !important;
}

/* Add a tooltip for disabled buttons */
.velocity-enhance-button:disabled:hover::after {
  content: attr(title);
  position: absolute;
  right: 100%;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  margin-right: 10px;
  z-index: 1000;
}

      .velocity-wrapper {
        position: relative !important;
        display: inline-block !important;
        width: 100% !important;
        overflow: hidden !important;
      }
      .velocity-enhance-button {
        position: absolute !important;
        top: 60% !important;
        right: 12px !important;
        transform: translateY(-50%) !important;
        width: 32px !important;
        height: 32px !important;
        padding: 6px !important;
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
      }
      .velocity-enhance-button:hover {
        background: black !important;
        box-shadow: 0 2px 8px rgba(0, 138, 203, 0.3) !important;
        transform: translateY(-50%) scale(1.05) !important;
      }
      .velocity-enhance-button.visible {
        opacity: 1 !important;
        pointer-events: auto !important;
      }
      .velocity-enhance-button:disabled.visible {
        opacity: 0.5 !important;
        cursor: not-allowed !important;
        transform: translateY(-50%) scale(1) !important;
        pointer-events: none !important;
      }
      .velocity-enhance-button img {
        width: 35px !important;
        height: 35px !important;
        transition: transform 0.2s ease !important;
        object-fit: contain !important;
      }
      .velocity-enhance-button:hover:not(:disabled) img {
        transform: scale(1.1) !important;
      }
      /* Add padding to prevent text overlap with button */
      .velocity-wrapper textarea,
      .velocity-wrapper [contenteditable="true"] {
        padding-right: 50px !important;
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
  
  async function handleCreditDeduction(feature) {
    const storage = await chrome.storage.local.get(['userId', 'token']);
    const userId = storage.userId;
    const token = storage.token;
    console.log("token:?"+token);
    try {
      // Get feature credits
      const creditsResponse = await fetch('http://127.0.0.1:3001/api/credit/credits', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const creditsData = await creditsResponse.json();
      const featureCredit = creditsData.data.find(credit => credit.feature === feature);
      
      if (!featureCredit) {
        throw new Error('Feature not found');
      }
  
      // Get user's token balance
      const balanceResponse = await fetch(`http://127.0.0.1:3001/api/token-types/${userId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const balanceData = await balanceResponse.json();
      const tokensReceived = balanceData.data.token_received;
      const tokensUsed = balanceData.data.tokens_used;
  
      if (tokensReceived <= tokensUsed) {
        throw new Error('Out of tokens');
      }
  
      if (tokensReceived - tokensUsed >= featureCredit.credits) {
        const updatedTokensUsed = tokensUsed + featureCredit.credits;
        
        // Update tokens
        await fetch(`http://127.0.0.1:3001/api/token-types/${userId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            tokens_used: updatedTokensUsed,
            token_received: tokensReceived
          })
        });
  
        return featureCredit.credits;
      } else {
        throw new Error('Not enough tokens');
      }
    } catch (error) {
      throw error;
    }
  }
  
  async function handleCreditDeductions(state) {
    try {
      // Basic prompt credit deduction
      await handleCreditDeduction('basic_prompt');
  
      // Style credit deduction if style is selected
      if (state.styleType) {
        await handleCreditDeduction('style_prompt');
      }
  
      // Platform credit deduction if platform is selected
      if (state.platform) {
        await handleCreditDeduction('platform');
      }
  
      return true;
    } catch (error) {
      console.error('Error handling credit deductions:', error);
      throw new Error('Error processing credits. Please contact support.');
    }
  }
  async function savePromptToHistory(promptText, aiType) {
    try {
      const storage = await chrome.storage.local.get(['userId', 'token']);
      const userId = storage.userId;
      const token = storage.token;
  
      if (!userId || !token) {
        throw new Error('User authentication required');
      }
  
      // Ensure aiType is a string
      const aiTypeString = String(aiType || 'General');
  
      const response = await fetch('http://127.0.0.1:3001/api/history/prompts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          user_id: userId,
          prompt_text: promptText,
          ai_type: aiTypeString,  // Convert to string
          tokens_used: 0
        })
      });
  
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.message);
      }
  
      return data;
    } catch (error) {
      console.error('Error saving prompt to history:', error);
      throw error;
    }
  }
  
  
  async function updatePromptTokens(promptId, tokensUsed) {
    try {
      const storage = await chrome.storage.local.get(['token']);
      const token = storage.token;
  
      if (!token) {
        throw new Error('User authentication required');
      }
  
      const response = await fetch(`http://127.0.0.1:3001/api/history/prompts/${promptId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          tokens_used: tokensUsed
        })
      });
  
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.message);
      }
  
      return data;
    } catch (error) {
      console.error('Error updating prompt tokens:', error);
      throw error;
    }
  }
  async function saveResponseToHistory(promptText, originalPromptId, aiType, tokensUsed) {
    try {
      const storage = await chrome.storage.local.get(['userId', 'token']);
      const userId = storage.userId;
      const token = storage.token;
  
      if (!userId || !token) {
        throw new Error('User authentication required');
      }
  
      // Ensure aiType is a string
      const aiTypeString = String(aiType || 'General');
  
      const response = await fetch('http://127.0.0.1:3001/api/history/responses', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          user_id: userId,
          prompt_text: promptText,
          original_prompt_id: originalPromptId,
          ai_type: aiTypeString,  // Convert to string
          tokens_used: tokensUsed || 0
        })
      });
  
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.message);
      }
  
      return data;
    } catch (error) {
      console.error('Error saving response to history:', error);
      throw error;
    }
  }
  
  function addCharacterLimitation(inputElement) {
    const CHAR_LIMIT = 1100;
    
    // Create character counter
    const charCounter = document.createElement('div');
    charCounter.className = 'velocity-char-counter';
    charCounter.style.cssText = `
      position: absolute;
      bottom: 8px;
      right: 48px;
      color: #666;
      font-size: 12px;
      pointer-events: none;
      user-select: none;
      background: transparent;
      z-index: 999999;
    `;
  
    // Handle all text changes
    function updateCharCount() {
      const text = inputElement.value || inputElement.textContent || '';
      const length = text.length;
      
      // Update counter
      charCounter.textContent = `${length}/${CHAR_LIMIT}`;
      
      // Update counter color based on length
      if (length > CHAR_LIMIT) {
        charCounter.style.color = '#ef4444';
      } else {
        charCounter.style.color = '#666';
      }
    }
  
    // Listen for all possible text input events
    inputElement.addEventListener('input', updateCharCount);  // Catches typing, pasting, cutting, deleting
    inputElement.addEventListener('keydown', updateCharCount); // Catches keyboard shortcuts
    inputElement.addEventListener('paste', updateCharCount);  // Specifically catch paste events
    inputElement.addEventListener('cut', updateCharCount);   // Specifically catch cut events
    inputElement.addEventListener('delete', updateCharCount); // Catch delete operations
    inputElement.addEventListener('change', updateCharCount); // Catch any other changes
    
    // Initialize counter
    updateCharCount();
    return charCounter;
  }
  
  
  // Function to handle prompt enhancement
  async function enhancePrompt(originalText) {
    try {
      const state = getState();
      let styleTransform = null;
      console.log("platform in state:"+state.platform)
      // Check if style type exists and is valid
      if (state.styleType && state.styleTransformations[state.styleType.toLowerCase()]) {
        styleTransform = state.styleTransformations[state.styleType.toLowerCase()];
      }
  
      const promptData = await savePromptToHistory(originalText, state.platform);
      lastSavedPromptId = promptData.data.history_id;
  
      await handleCreditDeductions(state);
      
      // Apply style transformation if valid
      const modifiedPrompt = styleTransform ? styleTransform.modifier(originalText) : originalText;
  
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
      console.log("raw response:"+response);
      //const response = {"prompts":[{"prompt":"Imagine a world where trial is not a test of guilt or innocence, but rather a ritual to awaken the hidden abilities of the accused. Design an immersive and surreal courtroom where the defendant's powers are revealed through an ancient dance, with each step unlocking a new dimension of their potential. The judge is an enigmatic being with the power to manipulate reality itself, using their gaze to guide the defendant through this transformative experience."},{"prompt":"Envision a futuristic city where trial has evolved into a high-stakes competition between rival factions vying for control. The defendants are advanced AI entities that have developed sentience, and their trials are broadcasted as spectacular events in zero-gravity arenas. Each faction must strategically deploy their unique technologies and cybernetic enhancements to outmaneuver and defeat their opponents in an intricate ballet of light, sound, and energy."},{"prompt":"In this post-apocalyptic wasteland, trial has become an ancient art form passed down through generations of survivors. The accused are presented before the 'Council of Elders', who evaluate their worthiness for membership in society by challenging them to create innovative solutions using scavenged materials from the ruins. As each member presents their creations, they must also navigate complex web-like puzzles that shift and adapt based on their successes or failures."}]}
      const data = await response.json();
      const parsedResponse = JSON.parse(data.json());
      //const parsedResponse = response;
  
      if (!parsedResponse.prompts || !parsedResponse.prompts.length) {
        throw new Error('No prompts received from server');
      }
  
      const enhancedPrompt = parsedResponse.prompts[0].prompt;
      await saveResponseToHistory(
        enhancedPrompt, 
        lastSavedPromptId,
        state.platform,
        lastTokensUsed
      );
  
      return enhancedPrompt;
    } catch (error) {
      console.error('Enhancement failed:', error);
      throw error;
    }
  }  // Function to create and attach enhance button
  function createEnhanceButton(inputElement) {
    const wrapper = document.createElement('div');
    wrapper.className = 'velocity-wrapper';
    inputElement.dataset.hasEnhanceButton = 'true';

    const charCounter = addCharacterLimitation(inputElement);

    const button = document.createElement('button');
    button.className = 'velocity-enhance-button';
    
    // Add token check before enabling the button
    chrome.storage.local.get(['token', 'isAuthenticated', 'userId'], async (result) => {
      if (!result.isAuthenticated || !result.token) {
        button.disabled = true;
        button.title = 'Please log in to use this feature';
        return;
      }
  
      try {
        const response = await fetch(`http://127.0.0.1:3001/api/token-types/${result.userId}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${result.token}`
          }
        });
        const data = await response.json();
        
        if (data.data.token_received <= data.data.tokens_used) {
          button.disabled = true;
          button.title = 'Insufficient tokens. Please purchase more tokens to continue.';
        }
      } catch (error) {
        console.error('Error checking tokens:', error);
        button.disabled = true;
        button.title = 'Error checking token balance';
      }
    });
      const platformInfo = window.velocityState.platformInfo;
    if (platformInfo?.platform) {
      wrapper.dataset.platform = platformInfo.platform;
    }


    // Position the wrapper correctly relative to the input
    const inputStyles = window.getComputedStyle(inputElement);
    wrapper.style.width = inputStyles.width;
    wrapper.style.height = inputStyles.height;
    // Create button with PNG image
    // Create and set up the image element
    const img = document.createElement('img');
    img.src = chrome.runtime.getURL('assets/logo.png'); // Make sure to update this path
    img.alt = 'Enhance';
    img.draggable = false; // Prevent image dragging
    button.appendChild(img);
    button.title = `Enhance ${platformInfo?.config?.name || ''} prompt`;
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

      if (!platformInfo?.isSupported) {
        console.log('Platform not supported, enhancement disabled');
        return;
      }

      const text = inputElement.value || inputElement.textContent || '';
      if (!text) return;
      
      // Check character limit before processing
      if (text.length > 1100) {
        button.style.background = 'linear-gradient(180deg, #FF4444 0%, #CC0000 100%)';
        setTimeout(() => {
          button.style.background = '';
        }, 1000);
        return;
      }
  
      
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
    wrapper.appendChild(charCounter); // Add the character counter
    wrapper.appendChild(button);
  }
  // Add visibility based on state
  if (window.velocityState?.isEnabled && platformInfo?.isSupported) {
    button.classList.add('visible');
  }
  // Handle resizing
  const resizeObserver = new ResizeObserver(() => {
    const styles = window.getComputedStyle(inputElement);
    wrapper.style.width = styles.width;
    wrapper.style.height = styles.height;
  });
  resizeObserver.observe(inputElement);
 }

 function shouldEnhanceInput(input) {
  if (input.closest('.velocity-wrapper') ||
      input.dataset.hasEnhanceButton === 'true' ||
      input.parentElement?.querySelector('.velocity-enhance-button')) {
    return false;
  }
  const style = window.getComputedStyle(input);
  return style.display !== 'none' &&
         style.visibility !== 'hidden' &&
         input.offsetParent !== null &&
         !input.disabled;
}

async function findAndEnhanceInputs() {
  const platformInfo = await detectPlatform();
  if (!platformInfo.isSupported) {
    console.log('Not a supported platform, skipping enhancement');
    cleanupEnhanceButtons();
    return;
  }
  if (!window.velocityState?.isEnabled) {
    console.log('Enhancement disabled, skipping');
    cleanupEnhanceButtons();
    return;
  }
  const inputs = document.querySelectorAll(platformInfo.config.selectors);
  console.log(`Found ${inputs.length} matching inputs for ${platformInfo.platform}`);
  inputs.forEach(input => {
    if (shouldEnhanceInput(input)) {
      createEnhanceButton(input);
    }
  });
}
function cleanupEnhanceButtons() {
  document.querySelectorAll('.velocity-wrapper').forEach(wrapper => {
    const input = wrapper.querySelector('textarea, [contenteditable="true"]');
    if (input) {
      input.dataset.hasEnhanceButton = 'false';
      wrapper.parentNode.insertBefore(input, wrapper);
      wrapper.remove();
    }
  });
}

// Message handler to update parameters from extension
// chrome.runtime.onMessage.addListener(async (message, sender, sendResponse) => {
//   if (message.action === 'updateEnhanceParameters') {
//     console.log('Updating enhancement parameters:', message);
//     const platformInfo = await detectPlatform();
//     window.velocityState = {
//       ...window.velocityState,
//       platformInfo: platformInfo,
//       styleType: message.style,
//       isEnabled: message.enabled && platformInfo.isSupported
//     };
//     if (window.velocityState.isEnabled && platformInfo.isSupported) {
//       findAndEnhanceInputs();
//     } else {
//       cleanupEnhanceButtons();
//     }
//     sendResponse({
//       success: true,
//       platformDetected: platformInfo.platform,
//       isSupported: platformInfo.isSupported
//     });
//   }
//   return true;
// });
  // Initial setup
  (async function() {
    const platformInfo = await detectPlatform();
    const currentState = window.velocityState || {};
    window.velocityState = {
      ...currentState,
      isEnabled: false,
      platformInfo: platformInfo,
      styleType: ''
    };
    if (platformInfo.isSupported) {
      // Set up observer for dynamic content
      const observer = new MutationObserver((mutations) => {
        const shouldScan = mutations.some(mutation =>
          Array.from(mutation.addedNodes).some(node =>
            node.nodeType === 1 && node.querySelector?.(platformInfo.config.selectors)
          )
        );
        if (shouldScan) {
          findAndEnhanceInputs();
        }
      });
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    }
  })();
})();
