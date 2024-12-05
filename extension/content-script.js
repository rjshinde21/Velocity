// contentScript.js
// This script runs in the context of the web page
(function() {
let lastAuthState = null;

// Function to check auth state
function checkAuthState() {
        // Get token first
        const token = localStorage.getItem('token');
        // console.log('Retrieved token:', token); // Debug log\
        // console.log("Retrieved email" , localStorage.getItem('userEmail'))
    
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

// Check auth state periodically
setInterval(checkAuthState, 1000);

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
      const creditsResponse = await fetch('http://127.0.0.1:3000/api/credit/credits', {
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
      const balanceResponse = await fetch(`http://127.0.0.1:3000/api/token-types/${userId}`, {
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
        await fetch(`http://127.0.0.1:3000/api/token-types/${userId}`, {
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
  
  // Function to handle prompt enhancement
  async function enhancePrompt(originalText) {
    try {
      const state = getState();
      let styleTransform;
      if(state.styleType!=null){
        styleTransform = state.styleTransformations[state.styleType.toLowerCase()];
      }
      else{
        styleTransform = "";
      }
     
  
      // Handle credit deductions before processing
      await handleCreditDeductions(state);
      let modifiedPrompt;
      if(styleTransform!=""){
      modifiedPrompt = styleTransform.modifier(originalText);
      }
      else{
        modifiedPrompt = originalText;
      }
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
  }  // Function to create and attach enhance button
  function createEnhanceButton(inputElement) {
    if (inputElement.dataset.hasEnhanceButton) return;
    // Create wrapper with proper positioning
    const wrapper = document.createElement('div');
    wrapper.className = 'velocity-wrapper';
    // Position the wrapper correctly relative to the input
    const inputStyles = window.getComputedStyle(inputElement);
    wrapper.style.width = inputStyles.width;
    wrapper.style.height = inputStyles.height;
    // Create button with PNG image
    const button = document.createElement('button');
    button.className = 'velocity-enhance-button';
    // Create and set up the image element
    const img = document.createElement('img');
    img.src = chrome.runtime.getURL('assets/logo.png'); // Make sure to update this path
    img.alt = 'Enhance';
    img.draggable = false; // Prevent image dragging
    button.appendChild(img);
    button.title = 'Enhance text'; // Add tooltip
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
   inputElement.parentNode.insertBefore(wrapper, inputElement);
   wrapper.appendChild(inputElement);
   wrapper.appendChild(button);
   // Add visibility based on state
   if (getState().isEnabled) {
     button.classList.add('visible');
   }
   inputElement.dataset.hasEnhanceButton = 'true';
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
  let selector;
  if(state.platform!=null)
  {
    selector = state.platformSelectors[state.platform.toLowerCase()]
  }
  else{
    selector = state.platformSelectors.general;
                  
  }
                  
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
// Message handler to update parameters from extension
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  try {
    if (message.action === 'updateEnhanceParameters') {
      const state = getState();
      // Update parameters in state
      state.platform = message.platform;
      state.styleType = message.style;
      state.isEnabled = message.enabled;
      console.log('Parameters updated:', {
        platform: state.platform,
        style: state.styleType,
        enabled: state.isEnabled
      });
      // Update UI
      findAndEnhanceInputs();
      updateButtonVisibility();
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
