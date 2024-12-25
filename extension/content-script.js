// contentScript.js
// This script runs in the context of the web page

(function() {

  let lastAuthState = null;
  let lastSavedPromptId = null;  // Add this at the top with your other state variables
  let lastTokensUsed = 0;
  let isValidPlatform = false;
  let hideTimeout;
  let CHAR_THRESHOLD_MESSAGE = 25;
  let helpMessageVisible = false;
  let hasStyleSelected = false;
  let loadingInterval;
  
  const HIDE_DELAY = 300; // 300ms delay
  function isDiscordPlatform() {
    const url = window.location.href;
    return /^https:\/\/(www\.)?discord\.com\/channels/.test(url);
  }
  
  function trackEvent(eventName, properties = {}) {
    chrome.runtime.sendMessage({
        type: 'TRACK_EVENT',
        eventName: eventName,
        properties: properties
    }, response => {
        if (response?.status === 'success') {
            console.log('Event tracked:', eventName);
        } else {
            console.error('Failed to track event:', eventName);
        }
    });
  }
  // Function to check auth state
  async function checkAuthState() {
    if (isDiscordPlatform()) {
      console.log('Skipping auth state check for Discord');
      return null;
    }
  
    if (!isValidPlatform) {
      return null;
    }
  

    const authData = {
      isAuthenticated: !!localStorage.getItem('token'),
      token: localStorage.getItem('token'),
      userId: localStorage.getItem('userId'),
      userName: localStorage.getItem('userName'),
      userEmail: localStorage.getItem('userEmail')
    };
  
    // Only send message if auth state has changed
    if (JSON.stringify(authData) !== JSON.stringify(lastAuthState) && 
        ((!localStorage.getItem('token') && !localStorage.getItem('userEmail')) || 
         (localStorage.getItem('token') && localStorage.getItem('userEmail')))) {
      
      await chrome.storage.local.set({
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
  
    return authData;
  }
  async function injectStyles() {
    const platformInfo = await detectPlatform();
    if (!platformInfo.isSupported) return;
  
    if (!document.querySelector('#velocity-inject-styles')) {
      try {
        const baseStyles = await fetch(chrome.runtime.getURL('src/velocity-inject.css'))
          .then(response => response.text());
        
        // Get platform-specific styles
        const platformStyles = platformInfo.config.customStyles || '';
  
        const styleElement = document.createElement('style');
        styleElement.id = 'velocity-inject-styles';
        styleElement.textContent = baseStyles + platformStyles;
        document.head.appendChild(styleElement);
      } catch (error) {
        console.error('Error injecting styles:', error);
      }
    }
  }
  function calculatePopupPosition(button, popup) {
    const buttonRect = button.getBoundingClientRect();
    const popupHeight = popup.offsetHeight;
    const viewportHeight = window.innerHeight;
    
    // Check if we're on Claude
    if (window.velocityState.platformInfo?.platform === 'claude') {
      // Calculate available space above and below
      const spaceAbove = buttonRect.top;
      const spaceBelow = viewportHeight - buttonRect.bottom;
      const MARGIN = 10;
      
      // Determine position only for Claude
      const position = spaceBelow >= popupHeight || spaceBelow > spaceAbove ? 'bottom' : 'top';
      
      // Position popup based on available space
      popup.style.position = 'fixed';
      popup.style.left = `${buttonRect.left + buttonRect.width/2}px`;
      
      if (position === 'bottom') {
        popup.style.bottom = '';
        popup.style.top = `${buttonRect.bottom + MARGIN}px`;
        //popup.style.transform = 'translateX(-50%)';
      } else {
        popup.style.bottom = `${window.innerHeight - buttonRect.top + MARGIN}px`;
        //popup.style.transform = 'translateX(-50%)';
      }
      
      return position;
    } else {
      // For all other platforms, keep the original positioning
      //popup.style.position = 'fixed';
      popup.style.left = `${buttonRect.left + buttonRect.width/2}px`;
      popup.style.bottom = `${window.innerHeight - buttonRect.top + 10}px`;
      //popup.style.transform = 'translateX(-50%)';
      return 'top'; // Default position for non-Claude platforms
    }
  }
  function notifyWelcomeMessageReady() {
    console.log("NOTIFY");
    chrome.runtime.sendMessage({
      type: 'WELCOME_BUTTON_READY'
    });
  }
  
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    
    if (message.action === 'toggleEnhanceButton') {
      window.velocityState.isEnabled = message.enabled;
      updateButtonVisibility();
    }
    
    if (message.type === 'AUTH_STATE_CHANGED') {
      if (isDiscordPlatform()) {
        console.log('Skipping auth state update for Discord');
        return;
      }
  
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
            const response = await fetch(`https://thinkvelocity.in/api/api/token-types/${userId}`, {
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
            await injectStyles();
            
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
    if (isDiscordPlatform()) {
      return; // Skip storage events for Discord
    }
  
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
      selectors: '.ProseMirror[contenteditable="true"][id="prompt-textarea"], textarea.resize-none.overflow-hidden.border-0.bg-transparent',
      name: 'GPT',
      customStyles: `
        .velocity-wrapper {
          display: grid !important;
          width: 100% !important;
          position: relative !important;
          min-height: 48px !important;
          height: auto !important;
        }
    
        .velocity-wrapper textarea {
          grid-column: 1 / -1 !important;
          grid-row: 1 / -1 !important;
          width: 100% !important;
          height: 100% !important;
          resize: none !important;
          overflow-y: hidden !important;
          padding-right: 45px !important;
          margin: 0 !important;
          border: 0 !important;
          background: transparent !important;
          box-sizing: border-box !important;
        }
    
        .velocity-wrapper .velocity-enhance-button {
          position: absolute !important;
          right: 12px !important;
          bottom: 8px !important;
          z-index: 10 !important;
        }
    
        .velocity-wrapper span.invisible {
          visibility: hidden !important;
          white-space: pre-wrap !important;
          grid-column: 1 / -1 !important;
          grid-row: 1 / -1 !important;
          padding: 0 !important;
        }
    
        /* Hide scrollbars */
        .velocity-wrapper *::-webkit-scrollbar {
          display: none !important;
          width: 0 !important;
          height: 0 !important;
        }
      `
    },
    claude: {
      urlPattern: /^https:\/\/claude\.ai/,
      selectors: '.claude-textarea, div[contenteditable="true"]',
      name: 'Claude',
      customStyles: `
      .velocity-wrapper {
        position: relative !important;
        display: block !important;
        width: 100% !important;
        min-height: 24px !important;
        background: transparent !important;
        overflow: hidden !important;
      }
      
      .velocity-wrapper textarea,
      .velocity-wrapper [contenteditable="true"] {
        padding-right: 45px !important;
        min-height: inherit !important;
        overflow: hidden !important;
        resize: none !important;
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
        background: transparent !important;
        width: 100% !important;
        box-sizing: border-box !important;
      }
    `  
    },
    gemini: {
      urlPattern: /^https:\/\/gemini\.google\.com/,
      selectors: '.ql-editor[contenteditable="true"][role="textbox"], .textarea[contenteditable="true"]',
      name: 'Gemini'
    },
    discord: {
      urlPattern: /^https:\/\/(www\.)?discord\.com\/channels/,
      selectors: '.markup_f8f345.editor_a552a6.slateTextArea_e52116, [class*="slateTextArea_"][role="textbox"]',
      name: 'Midjourney',
      customStyles: `
        .velocity-wrapper {
          position: relative !important;
          display: block !important;
          width: 100% !important;
        }
        
        .velocity-wrapper [role="textbox"] {
          padding-right: 50px !important;
        }
  
        .velocity-enhance-button {
          top: 50% !important;
          right: 12px !important;
          z-index: 999999 !important;
        }
      `
    },
    gama: {
      urlPattern: /^https:\/\/(www\.)?gamma\.app/,
      selectors: 'textarea, div[contenteditable="true"]',
      name: 'Gamma'
    },
    runway: {
      urlPattern: /^https:\/\/app\.runwayml\.com/,
      selectors: '.TextEditor-module__textbox__lvV8X, [data-lexical-editor="true"]',
      name: 'Runway',
      customStyles: `
      .velocity-wrapper {
        position: relative !important;
        display: block !important;
        width: 100% !important;
        min-height: 81px !important;
        height: auto !important;
      }
  
      .velocity-wrapper .TextEditor-module__textbox__lvV8X {
        padding-right: 50px !important;
        min-height: 81px !important;
        height: auto !important;
        max-height: none !important;
        overflow-y: visible !important;
        background: transparent !important;
        position: relative !important;
      }
  
      .velocity-wrapper .TextEditor-module__textbox__lvV8X p {
        margin: 0 !important;
        padding: 0 !important;
      }
  
      .velocity-enhance-button {
        position: absolute !important;
        top: 50% !important;
        right: 12px !important;
        transform: translateY(-50%) !important;
      }
    `
    },
    thinkvelocity: {
      urlPattern: /^https:\/\/(www\.)?thinkvelocity\.in/,
      selectors: 'textarea, div[contenteditable="true"]',
      name: 'ThinkVelocity',
      isDevelopment: true
    },
    localhost: {
      urlPattern: /^http:\/\/localhost:\d+/,
      selectors: 'textarea, div[contenteditable="true"]',
      name: 'Local Development',
      isDevelopment: true
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
    const loadingMessages = [
      `Enhancing your prompt to match your needs...`,
      `Crafting the perfect prompt for ${window.velocityState.platformInfo?.platform || 'your platform'}...`,
      `Working my magic on your prompt...`,
      `Transforming your prompt with ${window.velocityState.styleType} style...`,
      `Adding a touch of Velocity to your writing...`,
      `Optimizing your prompt for better results...`,
      `Crafting your enhanced prompt...`,
      `Making your prompt more impactful...`
    ];
    
    const getRandomLoadingMessage = () => {
      return loadingMessages[Math.floor(Math.random() * loadingMessages.length)];
    };
    
    
  async function detectPlatform() {
    try {
      const url = window.location.href;
      console.log('Checking URL:', url);
      
      // Early return if not a valid platform
      const isPlatformValid = Object.values(PLATFORM_CONFIG).some(config => 
        config.urlPattern.test(url)
      );
      
      if (!isPlatformValid) {
        isValidPlatform = false;
        return {
          isSupported: false,
          platform: null,
          config: null
        };
      }
  
      isValidPlatform = true;
      
      // Rest of your existing platform detection logic
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
      
      return {
        isSupported: false,
        platform: null,
        config: null
      };
    } catch (error) {
      console.error('Error in platform detection:', error);
      isValidPlatform = false;
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
   opacity: 0.5 !important;
      cursor: not-allowed !important;
    background-color: #666 !important;
  }
     @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
  
    .animate-spin {
      animation: spin 1s linear infinite;
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
    display: inline-flex !important;
    align-items: center !important;
    width: 100% !important;
    min-height: inherit !important;
    visibility: visible !important; /* Show immediately */
  }

  
  .velocity-wrapper.loaded {
    visibility: visible !important;
    opacity: 1 !important;
    transition: visibility 0s, opacity 0.2s ease !important;
  }
  
     .velocity-enhance-button {
    position: absolute !important;
    bottom: 8px !important;  // Changed from top positioning
    right: 12px !important;
    width: 32px !important;
    height: 32px !important;
    padding: 6px !important;
    background: transparent !important;
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
  }

        .velocity-enhance-button:hover {
          background: black !important;
          box-shadow: 0 2px 8px rgba(0, 138, 203, 0.3) !important;
          transform: scale(1.05) !important;
        }
        .velocity-wrapper.loaded .velocity-enhance-button.visible {
    opacity: 1 !important;
    pointer-events: auto !important;
  }
        .velocity-enhance-button:disabled.visible {
          opacity: 0.5 !important;
          cursor: not-allowed !important;
          transform:  scale(1) !important;
          pointer-events: none !important;
        }
          .velocity-enhance-button img {
    width: 35px !important;
    height: 35px !important;
    transition: transform 0.2s ease !important;
    object-fit: contain !important;
    background: transparent !important;
    display: block !important;
    filter: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
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
    async function validateCredits(state) {
      try {
        const storage = await chrome.storage.local.get(['userId', 'token']);
        const userId = storage.userId;
        const token = storage.token;
    
        if (!userId || !token) {
          throw new Error('User authentication required');
        }
    
        // Get feature credits first
        const creditsResponse = await fetch('https://thinkvelocity.in/api/api/credit/credits', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        const creditsData = await creditsResponse.json();
    
        // Calculate total required credits
        let totalRequiredCredits = 0;
    
        // Basic prompt credits
        const basicPromptCredit = creditsData.data.find(credit => credit.feature === 'basic_prompt');
        if (!basicPromptCredit) throw new Error('Basic prompt feature not found');
        totalRequiredCredits += basicPromptCredit.credits;
    
        // Style credits if style is selected
        if (state.styleType && state.styleType !== '') {
          const styleCredit = creditsData.data.find(credit => credit.feature === 'style_prompt');
          if (!styleCredit) throw new Error('Style feature not found');
          totalRequiredCredits += styleCredit.credits;
        }
    
        // Platform credits if platform is selected
        if (state.platform && state.platform !== '') {
          const platformCredit = creditsData.data.find(credit => credit.feature === 'platform');
          if (!platformCredit) throw new Error('Platform feature not found');
          totalRequiredCredits += platformCredit.credits;
        }
    
        // Get user's token balance
        const balanceResponse = await fetch(`https://thinkvelocity.in/api/api/token-types/${userId}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        const balanceData = await balanceResponse.json();
        const tokensReceived = balanceData.data.token_received;
        const tokensUsed = balanceData.data.tokens_used;
        const availableTokens = tokensReceived - tokensUsed;
    
        if (availableTokens < totalRequiredCredits) {
          throw new Error('Insufficient tokens available');
        }
    
        return {
          success: true,
          requiredCredits: totalRequiredCredits,
          availableTokens: availableTokens
        };
      } catch (error) {
        console.error('Credit validation failed:', error);
        throw error;
      }
    }
    
    async function deductCredits(state, creditsToDeduct) {
      const storage = await chrome.storage.local.get(['userId', 'token']);
      const userId = storage.userId;
      const token = storage.token;
    
      const balanceResponse = await fetch(`https://thinkvelocity.in/api/api/token-types/${userId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const balanceData = await balanceResponse.json();
      
      const updatedTokensUsed = balanceData.data.tokens_used + creditsToDeduct;
      
      await fetch(`https://thinkvelocity.in/api/api/token-types/${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          tokens_used: updatedTokensUsed,
          token_received: balanceData.data.token_received
        })
      });
    }
    
  
  // Modified createWelcomeMessage function with proper initialization
  // Modify createWelcomeMessage to be more reliable
// function createWelcomeMessage() {
//   // Check if message should be shown
//   chrome.storage.local.get(['welcomeMessageShown'], async function(result) {
//     if (result.welcomeMessageShown) {
//       return;
//     }

//     // Remove any existing welcome messages first
//     document.querySelectorAll('#velocity-welcome').forEach(el => el.remove());
//     const platformInfo = await detectPlatform();
    
//     // Don't show welcome message on ThinkVelocity or unsupported platforms
//     if (!platformInfo.isSupported || 
//         platformInfo.platform === 'thinkvelocity' || 
//         platformInfo.isDevelopment) {
//       return;
//     }

//     // Create initial welcome message
//     const welcomeBox = document.createElement('div');
//     welcomeBox.id = 'velocity-welcome';
//     welcomeBox.style.cssText = `
//       position: fixed;
//       top: 48px;
//       right: 16px;
//       width: 220px;
//       background: white;
//       border-radius: 12px;
//       box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
//       padding: 12px;
//       z-index: 2147483647;
//       font-family: system-ui, -apple-system, sans-serif;
//       animation: slideIn 0.3s ease-out;
//       border: 1px solid #E5E7EB;
//       cursor: pointer;
//       transition: all 0.2s ease;
//       opacity: 0;
//     `;

//     // Add content
//     welcomeBox.innerHTML = `
//       <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
//         <img src="${chrome.runtime.getURL('assets/logo.png')}" 
//              style="width: 20px; height: 20px;" alt="Velocity">
//         <span style="font-weight: 500; color: #1a1a1a;">Velocity Activated</span>
//       </div>
//       <p style="margin: 0; font-size: 12px; color: #666; line-height: 1.4;">
//         Ready to enhance your prompts on this site
//       </p>
//       <div style="display: flex; align-items: center; margin-top: 8px; gap: 4px;">
//         <span style="font-size: 12px; color: #666;">1/2</span>
//         <div style="flex-grow: 1; display: flex; gap: 4px; justify-content: flex-end;">
//           <div style="width: 8px; height: 8px; border-radius: 50%; background: #0284C7;"></div>
//           <div style="width: 8px; height: 8px; border-radius: 50%; background: #E5E7EB;"></div>
//         </div>
//       </div>
//     `;

//     // Add hover effects
//     welcomeBox.addEventListener('mouseover', () => {
//       welcomeBox.style.transform = 'scale(1.02)';
//     });

//     welcomeBox.addEventListener('mouseout', () => {
//       welcomeBox.style.transform = 'scale(1)';
//     });

//     // Ensure styles exist before adding the box
//     const ensureStyles = () => {
//       if (!document.querySelector('#velocity-welcome-styles')) {
//         const styleSheet = document.createElement('style');
//         styleSheet.id = 'velocity-welcome-styles';
//         styleSheet.textContent = `
//           @keyframes slideIn {
//             from { opacity: 0; transform: translateY(-16px); }
//             to { opacity: 1; transform: translateY(0); }
//           }
//           @keyframes slideOut {
//             from { opacity: 1; transform: translateY(0); }
//             to { opacity: 0; transform: translateY(-16px); }
//           }
//               @keyframes slideInUp {
//     from { 
//       opacity: 0; 
//       transform: translate(-50%, 16px);
//     }
//     to { 
//       opacity: 1; 
//       transform: translate(-50%, 0);
//     }
//   }
  
//   @keyframes slideOutDown {
//     from { 
//       opacity: 1; 
//       transform: translate(-50%, 0);
//     }
//     to { 
//       opacity: 0; 
//       transform: translate(-50%, 16px);
//     }
//   }

//         `;
//         document.head.appendChild(styleSheet);
//       }
//     };

// //    Function to add the welcome box
//     const addWelcomeBox = () => {
//       ensureStyles();
//       document.body.appendChild(welcomeBox);
//       // Trigger animation after a short delay
//       requestAnimationFrame(() => {
//         welcomeBox.style.opacity = '1';
//       });
//     };

//     // Try to add the welcome box immediately if document.body exists
//     if (document.body) {
//       addWelcomeBox();
//     } else {
//       // If document.body doesn't exist yet, wait for it
//       const observer = new MutationObserver((mutations, obs) => {
//         if (document.body) {
//           addWelcomeBox();
//           obs.disconnect();
//         }
//       });
      
//       observer.observe(document.documentElement, {
//         childList: true,
//         subtree: true
//       });
//     }

//     // Handle click to show second message and remove first message
//     // welcomeBox.addEventListener('click', () => {
//     //   welcomeBox.style.animation = 'slideOut 0.3s ease-in forwards';
//     //   setTimeout(() => {
//     //     welcomeBox.remove();
//     //     setTimeout(() => {
//     //       showSecondMessage();
//     //     }, 500); // Give time for enhance button to be injected
//     //   }, 300);
//     // });
//     setTimeout(() => {
//       if (welcomeBox && welcomeBox.parentNode) {
//         welcomeBox.style.animation = 'slideOut 0.3s ease-in forwards';
//         setTimeout(() => {
//           welcomeBox.remove();
//           // Show second message after first disappears
//           showSecondMessage();
//         }, 300);
//       }
//     }, 4000);

//     // Mark as shown
//     chrome.storage.local.set({ welcomeMessageShown: true });

//     // Auto-remove after 8 seconds if not clicked
//     // setTimeout(() => {
//     //   if (welcomeBox && welcomeBox.parentNode) {
//     //     welcomeBox.style.animation = 'slideOut 0.3s ease-in forwards';
//     //     setTimeout(() => welcomeBox.remove(), 3000);
//     //   }
//     // }, 8000);
//   });
// }
  
//   // Modified showSecondMessage function with better error handling
//   function showSecondMessage() {
//     console.log("SHOW SECOND MESSASGE");
//     let retryCount = 0;
//     const maxRetries = 10; // Increase max retries
//     const retryInterval = 1000; // Check every second
  
//     function findInputAndButton() {
//       const inputs = document.querySelectorAll('textarea, [contenteditable="true"], [role="textbox"]');
//       let targetInput = null;
//       let enhanceButton = null;
  
//       inputs.forEach(input => {
//         // Find the most visible input that has an enhance button
//         if (input.offsetParent !== null) { // Check if input is visible
//           const wrapper = input.closest('.velocity-wrapper');
//           if (wrapper) {
//             const button = wrapper.querySelector('.velocity-enhance-button');
//             if (button) {
//               targetInput = input;
//               enhanceButton = button;
//             }
//           }
//         }
//       });
  
//       return { input: targetInput, button: enhanceButton };
//     }
  
//     function attemptToShowMessage() {
//       const { input, button } = findInputAndButton();
      
//       if (input && button) {
//         // Remove any existing second messages
//         document.querySelectorAll('#velocity-welcome-2').forEach(el => el.remove());
  
//         const secondMessage = document.createElement('div');
//         secondMessage.id = 'velocity-welcome-2';
//         secondMessage.style.cssText = `
//           position: absolute;
//           bottom: calc(100% + 16px);
//           left: 50%;
//           transform: translateX(-50%);
//           width: 280px;
//           background: white;
//           border-radius: 12px;
//           box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
//           padding: 16px;
//           z-index: 2147483647;
//           font-family: system-ui, -apple-system, sans-serif;
//           animation: slideInUp 0.3s ease-out;
//           border: 1px solid #E5E7EB;
//           opacity: 0;
//           pointer-events: none;
//         `;
  
//         secondMessage.innerHTML = `
//           <div style="position: relative">
//             <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
//               <span style="font-weight: 500; color: #1a1a1a;">Enhance Your Prompts</span>
//             </div>
//             <p style="margin: 0; font-size: 12px; color: #666; line-height: 1.4;">
//               Click the enhance button that appears when you type to get AI-powered prompt improvements. Try writing a prompt and look for the button on the right!
//             </p>
//             <div style="display: flex; align-items: center; margin-top: 8px; gap: 4px;">
//               <span style="font-size: 12px; color: #666;">2/2</span>
//               <div style="flex-grow: 1; display: flex; gap: 4px; justify-content: flex-end;">
//                 <div style="width: 8px; height: 8px; border-radius: 50%; background: #E5E7EB;"></div>
//                 <div style="width: 8px; height: 8px; border-radius: 50%; background: #0284C7;"></div>
//               </div>
//             </div>
//             <div style="position: absolute; bottom: -28px; left: 50%; transform: translateX(-50%) rotate(45deg); width: 12px; height: 12px; background: white; border-right: 1px solid #E5E7EB; border-bottom: 1px solid #E5E7EB;"></div>
//           </div>
//         `;
  
//         const wrapper = input.closest('.velocity-wrapper');
//         if (wrapper) {
//           wrapper.style.position = 'relative';
//           wrapper.appendChild(secondMessage);
  
//           // Show message with animation
//           requestAnimationFrame(() => {
//             secondMessage.style.opacity = '1';
//           });
  
//           // Auto-remove after delay
//           setTimeout(() => {
//             if (secondMessage.parentNode) {
//               secondMessage.style.animation = 'slideOutDown 0.3s ease-in forwards';
//               setTimeout(() => secondMessage.remove(), 300);
//             }
//           }, 8000);
  
//           return true; // Successfully showed message
//         }
//       }
  
//       return false; // Failed to show message
//     }
  
//     function tryShowMessage() {
//       if (retryCount < maxRetries) {
//         if (!attemptToShowMessage()) {
//           retryCount++;
//           setTimeout(tryShowMessage, retryInterval);
//         }
//       }
//     }
  
//     // Start trying to show the message
//     tryShowMessage();
//   }
  
  
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
    
        const response = await fetch('https://thinkvelocity.in/api/api/history/prompts', {
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
    
        const response = await fetch(`https://thinkvelocity.in/api/api/history/prompts/${promptId}`, {
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
    
        const response = await fetch('https://thinkvelocity.in/api/api/history/responses', {
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
      const CHAR_THRESHOLD = 900;
      const CHAR_LIMIT = 1100;
      
      const charCounter = document.createElement('div');
      charCounter.className = 'velocity-char-counter';
      charCounter.style.cssText = `
        position: absolute !important;
        bottom: 8px !important;
        right: 48px !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        pointer-events: none !important;
        user-select: none !important;
        background: transparent !important;
        z-index: 999999 !important;
        opacity: 0 !important;
        transition: opacity 0.2s ease, color 0.2s ease !important;
      `;
    
      function updateCharCount() {
        const text = inputElement.value || inputElement.textContent || '';
        const length = text.length;
        
        charCounter.textContent = `${length}/${CHAR_LIMIT}`;
        
        if (length > CHAR_LIMIT) {
          charCounter.style.cssText += `
            opacity: 1 !important;
            color: #FF0000 !important;
          `;
          console.log('Setting red color', charCounter.style.color); // Debug log
        } else if (length > CHAR_THRESHOLD) {
          charCounter.style.cssText += `
            opacity: 1 !important;
            color: #FFA500 !important;
          `;
          console.log('Setting orange color', charCounter.style.color); // Debug log
        } else {
          charCounter.style.cssText += `
            opacity: 0 !important;
            color: #666666 !important;
          `;
        }
      }
    
      // Initial style setup
      updateCharCount();
    
      // Event listeners
      const events = ['input', 'keydown', 'paste', 'cut', 'delete', 'change'];
      events.forEach(event => {
        inputElement.addEventListener(event, updateCharCount);
      });
      
      return charCounter;
    }
  
    // Function to handle prompt enhancement
    async function enhancePrompt(originalText) {
      console.log("enhancing");
      
    //   trackContentEvent('Enhance Prompt', {
    //     title: "Enhance Prompt"
    // });
        
  
  
  
      try {
        const state = getState();
        let styleTransform = null;
        console.log("style in state:"+state.styleType);
        console.log("platform in state:"+state.platform);
        trackEvent('Enhance Button clicked', {
          platform:state.platform,
          style:state.styleType,
          promptLength: originalText.length
      });
      const creditValidation = await validateCredits(state);
  
        // Check if style type exists and is valid
        if (state.styleType && state.styleTransformations[state.styleType.toLowerCase()]) {
          styleTransform = state.styleTransformations[state.styleType.toLowerCase()];
        }
    
        const promptData = await savePromptToHistory(originalText, state.platform);
        lastSavedPromptId = promptData.data.history_id;
      
        // Apply style transformation if valid
        const modifiedPrompt = styleTransform ? styleTransform.modifier(originalText) : originalText;
        const formData = new FormData();
        const requestData = {
          prompt: modifiedPrompt,
          style: state.styleType,
          AIType: state.platform,
          singlePrompt: true
        };
          formData.append('data', JSON.stringify(requestData));
        const response = await fetch('https://thinkvelocity.in/python-api/process', {
          method: 'POST',
          body: formData,
        });
        console.log("raw response:"+response);
        const data = await response.json();
        console.dir("response data"+data.response);
        const parsedResponse = data.response;
        let prompts;
        if (typeof parsedResponse === 'string') {
          try {
            prompts = JSON.parse(parsedResponse).prompts;
            
          } catch (e) {
            // If it's not JSON, treat it as a single response
            prompts = [{ prompt: parsedResponse }];
          }
        } else if (parsedResponse.prompts) {
          prompts = parsedResponse.prompts;
        } else if (Array.isArray(parsedResponse)) {
          prompts = parsedResponse;
        } else {
          prompts = [{ prompt: String(parsedResponse) }];
        }
        //const parsedResponse = response;
    
        if (!parsedResponse.prompts || !parsedResponse.prompts.length) {
          throw new Error('No prompts received from server');
        }
        await deductCredits(state, creditValidation.requiredCredits);
  
        trackEvent('Response Generated',
          {
            location: "Enhance Button",
            length: parsedResponse.prompts.length
          }
        );
        const enhancedPrompt = parsedResponse.prompts[0].prompt;
        console.log("prompt length:"+parsedResponse.prompts.length);
        await saveResponseToHistory(
          enhancedPrompt, 
          lastSavedPromptId,
          state.platform,
          lastTokensUsed
        );
        return enhancedPrompt;
      } catch (error) {
        console.log("error:"+error);
        trackEvent('Generate Error', {
          error: error.message,
          platform:getState().platform,
          style:getState().styleType,
          location:"Enhance Button"
      });
        console.error('Enhancement failed:', error);
        throw error;
      }
    }  // Function to create and attach enhance button
    function calculatePopupPosition(button, popup) {
      const buttonRect = button.getBoundingClientRect();
      const popupHeight = popup.offsetHeight;
      const viewportHeight = window.innerHeight;
      
      // Calculate available space above and below
      const spaceAbove = buttonRect.top;
      const spaceBelow = viewportHeight - buttonRect.bottom;
      
      // Add some padding for better appearance
      const MARGIN = 10;
      
      // Determine if popup should go above or below based on available space
      const position = spaceBelow >= popupHeight || spaceBelow > spaceAbove ? 'bottom' : 'top';
      
      // Position popup
      popup.style.position = 'fixed';
      popup.style.left = `${buttonRect.left + buttonRect.width/2}px`;
      
      if (position === 'bottom') {
        popup.style.bottom = '';  // Clear bottom positioning
        popup.style.top = `${buttonRect.bottom + MARGIN}px`;
        popup.style.transform = 'translateX(-50%)';
      } else {
        popup.style.top = '';  // Clear top positioning
        popup.style.bottom = `${window.innerHeight - buttonRect.top + MARGIN}px`;
        popup.style.transform = 'translateX(-50%)';
      }
      
      return position;
    }
    
    function handleButtonHover(button, popup) {
      // Add hover related styles
      const hoverStyles = document.createElement('style');
      hoverStyles.textContent = `
        .velocity-enhance-button:not(.loading):hover + .velocity-popup,
        .velocity-popup:hover {
          opacity: 1 !important;
          visibility: visible !important;
          pointer-events: auto !important;
        }
    
        .velocity-enhance-button.loading:hover + .velocity-popup {
          opacity: 0 !important;
          visibility: hidden !important;
          pointer-events: none !important;
        }
    
        .velocity-popup {
          opacity: 0 !important;
          visibility: hidden !important;
          pointer-events: none !important;
          transition: opacity 0.3s ease, visibility 0.3s ease !important;
          z-index: 999999 !important;
        }
    
        .velocity-popup.show {
          opacity: 1 !important;
          visibility: visible !important;
          pointer-events: auto !important;
        }
      `;
      document.head.appendChild(hoverStyles);
    
      // Position the popup whenever button position changes
      const updatePopupPosition = () => {
        const buttonRect = button.getBoundingClientRect();
        popup.style.left = `${buttonRect.left + buttonRect.width/2}px`;
        popup.style.bottom = `${window.innerHeight - buttonRect.top + 10}px`;
      };
    
      // Update position on scroll and resize
      window.addEventListener('scroll', updatePopupPosition, { passive: true });
      window.addEventListener('resize', updatePopupPosition, { passive: true });
    
      // Initial position
      updatePopupPosition();
    
      return {
        forceHide: () => {
          popup.classList.remove('show');
        },
        updatePosition: updatePopupPosition
      };
    }
    
    function autoResizeTextarea(textarea) {
      if (!textarea) return;
      
      // Create or get the hidden span if it doesn't exist
      let hiddenSpan = textarea.parentElement.querySelector('span.invisible');
      if (!hiddenSpan) {
        hiddenSpan = document.createElement('span');
        hiddenSpan.className = 'invisible col-start-1 col-end-2 row-start-1 row-end-2 whitespace-pre-wrap p-0';
        textarea.parentElement.appendChild(hiddenSpan);
      }
    
      // Update hidden span content
      hiddenSpan.textContent = textarea.value + ' ';
      
      // Update textarea height based on content
      const computedStyle = window.getComputedStyle(hiddenSpan);
      const height = Math.max(
        parseInt(computedStyle.height),
        48 // minimum height
      );
      
      textarea.style.height = `${height}px`;
      textarea.parentElement.style.height = `${height}px`;
    }
    
    async function createEnhanceButton(inputElement) {
      const wrapper = document.createElement('div');
      wrapper.className = 'velocity-wrapper';
      // if (window.velocityState.platformInfo?.platform === 'chatgpt') {
      //   wrapper.style.display = 'grid';
        
      //   // Create hidden span for measuring text
      //   const hiddenSpan = document.createElement('span');
      //   hiddenSpan.className = 'invisible col-start-1 col-end-2 row-start-1 row-end-2 whitespace-pre-wrap p-0';
      //   wrapper.appendChild(hiddenSpan);
        
      //   // Add resize observer
      //   const resizeObserver = new ResizeObserver(() => {
      //     autoResizeTextarea(inputElement);
      //   });
      //   resizeObserver.observe(inputElement);
        
      //   // Add input listener for content changes
      //   inputElement.addEventListener('input', () => {
      //     autoResizeTextarea(inputElement);
      //   });
      // }
    
      const platformInfo = window.velocityState.platformInfo;
      const isClaudeInput = platformInfo?.platform === 'claude';


       // Apply platform-specific wrapper styles
  if (isClaudeInput) {
    wrapper.style.cssText += `
      position: relative !important;
      display: block !important;
      width: 100% !important;
      min-height: ${inputElement.offsetHeight}px !important;
      margin: 0 !important;
      background: transparent !important;
    `;

    // Preserve Claude's input styles
    const computedStyle = window.getComputedStyle(inputElement);
    inputElement.style.cssText += `
      width: 100% !important;
      min-height: inherit !important;
      padding-right: ${parseInt(computedStyle.paddingRight) + 40}px !important;
      box-sizing: border-box !important;
      background: transparent !important;
      overflow: hidden !important;
      resize: none !important;
    `;
  }

  // Handle input resizing for Claude
  if (isClaudeInput) {
    const resizeObserver = new ResizeObserver(() => {
      const height = inputElement.scrollHeight;
      wrapper.style.minHeight = `${height}px`;
      inputElement.style.height = `${height}px`;
    });
    resizeObserver.observe(inputElement);
  }

      if (window.velocityState.platformInfo?.platform === 'discord') {
        wrapper.style.cssText = `
            position: relative !important;
            display: block !important;
            width: 100% !important;
            min-height: ${inputElement.offsetHeight}px !important;
            margin: 0 !important;
        `;
        
        // Preserve Discord's input styles
        const computedStyle = window.getComputedStyle(inputElement);
        inputElement.style.cssText += `
            width: 100% !important;
            min-height: inherit !important;
            padding-right: ${parseInt(computedStyle.paddingRight) + 40}px !important;
            box-sizing: border-box !important;
            white-space: pre-wrap !important;
            overflow-wrap: break-word !important;
        `;
    }
  
      wrapper.style.cssText = `
          position: relative !important;
          display: inline-block !important;
          width: auto !important;
          min-width: 100% !important;
      `;
      inputElement.dataset.hasEnhanceButton = 'true';
      const computedStyle = window.getComputedStyle(inputElement);
      wrapper.style.cssText = `
      min-height: ${computedStyle.height} !important;
      height: auto !important;
    `;
  
      const originalStyles = {
          width: computedStyle.width,
          height: computedStyle.height,
          margin: computedStyle.margin,
          padding: computedStyle.padding,
          border: computedStyle.border,
          borderRadius: computedStyle.borderRadius,
          background: computedStyle.background,
          font: computedStyle.font
      };
      wrapper.style.minHeight = originalStyles.height;
      inputElement.style.cssText += `
      width: 100% !important;
      margin: 0 !important;
      box-sizing: border-box !important;
      padding-right: ${parseInt(computedStyle.paddingRight) + 40}px !important;
  `;
  const popup = document.createElement('div');
  popup.className = 'velocity-popup';
  const messageEl = document.createElement('div');
  messageEl.className = 'velocity-message';
  popup.style.opacity = '0';
  popup.style.visibility = 'hidden';
  popup.appendChild(messageEl);
  wrapper.appendChild(popup);
  
  // Wait for next frame to ensure button is positioned
  requestAnimationFrame(() => {
    // Wait another frame to be extra sure
    requestAnimationFrame(async() => {
      const buttonRect = button.getBoundingClientRect();
      if (buttonRect.height > 0) { // Check if button has been rendered
        popup.style.position = 'fixed';
        popup.style.left = `${buttonRect.left + buttonRect.width/2}px`;
        popup.style.bottom = `${window.innerHeight - buttonRect.top + 10}px`;
        popup.style.transform = 'translateX(-50%)';
        const result = await chrome.storage.local.get(['welcomeMessageShown','userName']);
        if (!result.welcomeMessageShown) {
          // First time message
          messageEl.textContent = 'Click the enhance button to optimize your prompts instantly';
          
          // Mark as shown after 8 seconds
          setTimeout(() => {
            chrome.storage.local.set({ welcomeMessageShown: true });
            // Update to regular message
            messageEl.textContent = `Hey ${result.userName}, I am Velocity. Your personal magician!`;
          }, 8000);
        } else {
          // Regular message for returning users
          messageEl.textContent = `Hey ${result.userName}, I am Velocity. Your personal magician!`;
        }
            popup.style.opacity = '1';
        popup.style.visibility = 'visible';
        popup.classList.add('show');
      }
    });
  });
  
      const charCounter = addCharacterLimitation(inputElement);
  
      const button = document.createElement('button');
      button.className = 'velocity-enhance-button';
      button.style.cssText += `
        background: transparent !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
      `;

      if (window.velocityState?.isEnabled) {
        button.classList.add('visible');
      }
      notifyWelcomeMessageReady();

      const hoverHandler = handleButtonHover(button, popup);
      // Add token check before enabling the button
      chrome.storage.local.get(['token', 'isAuthenticated', 'userId'], async (result) => {
        if (!result.isAuthenticated || !result.token) {
          button.disabled = true;
          button.title = 'Please log in to use this feature';
          return;
        }
    
        try {
          const response = await fetch(`https://thinkvelocity.in/api/api/token-types/${result.userId}`, {
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
        // const platformInfo = window.velocityState.platformInfo;
      if (platformInfo?.platform) {
        wrapper.dataset.platform = platformInfo.platform;
      }
  
  
      // Position the wrapper correctly relative to the input
      const inputStyles = window.getComputedStyle(inputElement);
      wrapper.style.width = inputStyles.width;
      wrapper.style.height = inputStyles.height;
      const img = document.createElement('img');
      img.src = chrome.runtime.getURL('assets/logo.png'); // Make sure to update this path
      img.alt = 'Enhance';
      img.draggable = false; // Prevent image dragging
      img.style.cssText = `
        width: 35px !important;
        height: 35px !important;
        transition: transform 0.2s ease !important;
        object-fit: contain !important;
        background: transparent !important; /* Ensure no background */
        display: block !important;
        filter: brightness(1) !important; /* Ensure no filter is adding white */
      `;

      button.appendChild(img);
      button.title = `Enhance ${platformInfo?.config?.name || ''} prompt`;
      // Add loading state handling
      const showLoading = () => {
       
        // const wrapper = button.closest('.velocity-wrapper');
        // if (wrapper) {
        //   wrapper.classList.add('loading');
        // }
        interactions.forceHide();
        button.classList.add('loading'); 
        button.disabled = true;
        // button.style.pointerEvents = 'none';
        // button.style.opacity = '0.5'; // Make it look disabled
             
        img.classList.add('animate-spin');
        hoverHandler.forceHide(); // Force hide popup when loading starts
        const showLoadingMessage = () => {
          const buttonRect = button.getBoundingClientRect();
          if (window.velocityState.platformInfo?.platform != 'claude') {
  
            popup.style.left = `${buttonRect.left + buttonRect.width/2}px`;
            popup.style.bottom = `${window.innerHeight - buttonRect.top + 10}px`;
          }  
          else{
          const position = calculatePopupPosition(button, popup);
          popup.classList.remove('top', 'bottom');
          popup.classList.add(position);
          }
  
          // popup.style.left = `${buttonRect.left + buttonRect.width/2}px`;
          // popup.style.bottom = `${window.innerHeight - buttonRect.top + 10}px`;
          
          // Get random loading message
          messageEl.textContent = getRandomLoadingMessage();
          popup.classList.add('show');
          messageEl.style.display = 'block';
          settingsSection.classList.remove('show');
        };
      
        showLoadingMessage();
        loadingInterval = setInterval(showLoadingMessage, 2000);
      };
  
  
      const hideLoading = () => {
    clearInterval(loadingInterval);
    button.disabled = false;
    if (window.velocityState.isEnabled) {
      button.style.pointerEvents = 'auto';
    }
    button.style.opacity = '1';
    button.classList.remove('loading');  
    img.classList.remove('animate-spin');
    popup.classList.remove('show');
  };
      
  // button.addEventListener('click', async (e) => {
  //   e.preventDefault();
  //   e.stopPropagation();
  
  //   if (!platformInfo?.isSupported) return;
  
  //   const selectedText = getSelectedText(inputElement);
  //   const fullText = inputElement.value || inputElement.textContent || '';
    
  //   if (!selectedText && !fullText) return;
  
  //   try {
  //     showLoading();
  //     const textToEnhance = selectedText || fullText;
  //     const enhancedText = await enhancePrompt(textToEnhance);
  
  //     // Handle different input types
  //     if (selectedText) {
  //       if (inputElement.tagName === 'TEXTAREA' || inputElement.tagName === 'INPUT') {
  //         const selectionStart = inputElement.selectionStart;
  //         const selectionEnd = inputElement.selectionEnd;
  //         inputElement.value = fullText.substring(0, selectionStart) + 
  //                            enhancedText + 
  //                            fullText.substring(selectionEnd);
  //         inputElement.selectionStart = selectionStart;
  //         inputElement.selectionEnd = selectionStart + enhancedText.length;
  //       } else {
  //         const selection = window.getSelection();
  //         if (selection.rangeCount > 0) {
  //           const range = selection.getRangeAt(0);
  //           range.deleteContents();
  //           range.insertNode(document.createTextNode(enhancedText));
  //         }
  //       }
  //     } else {
  //       if (inputElement.value !== undefined) {
  //         inputElement.value = enhancedText;
  //       } else {
  //         // Handle contenteditable
  //         inputElement.textContent = enhancedText;
  //       }
  //     }
  
  //     // Trigger input events for all platforms
  //     const inputEvent = new Event('input', { bubbles: true });
  //     inputElement.dispatchEvent(inputEvent);
      
  //     // Additional events for Claude
  //     if (platformInfo?.platform === 'claude') {
  //       const changeEvent = new Event('change', { bubbles: true });
  //       inputElement.dispatchEvent(changeEvent);
        
  //       // Trigger focus if needed
  //       inputElement.focus();
        
  //       // Force Claude's internal update
  //       if (inputElement.getAttribute('contenteditable') === 'true') {
  //         const keyEvent = new KeyboardEvent('keyup', {
  //           bubbles: true,
  //           key: 'Space',
  //           keyCode: 32
  //         });
  //         inputElement.dispatchEvent(keyEvent);
  //       }
  //     }
  
  //   } catch (error) {
  //     console.error('Enhancement failed:', error);
  //     // Show error message in popup
  //     const messageEl = document.querySelector('.velocity-message');
  //     if (messageEl) {
  //       messageEl.textContent = 'Enhancement failed. Please try again.';
  //       messageEl.style.color = '#ff4444';
  //       setTimeout(() => {
  //         messageEl.style.color = '';
  //       }, 3000);
  //     }
  //   } finally {
  //     hideLoading();
  //     updateButtonAnimations(button, inputElement);
  //   }
  // });

// Add helper function for getting selected text
function getSelectedText(element) {
  if (element.tagName === 'TEXTAREA' || element.tagName === 'INPUT') {
    return element.value.substring(element.selectionStart, element.selectionEnd);
  } else if (element.getAttribute('contenteditable') === 'true') {
    const selection = window.getSelection();
    if (selection.rangeCount > 0) {
      const range = selection.getRangeAt(0);
      if (element.contains(range.commonAncestorContainer)) {
        return selection.toString();
      }
    }
  }
  return '';
}

     // Set up proper DOM structure
     if (!inputElement.closest('.velocity-wrapper')) {
      inputElement.parentNode.insertBefore(wrapper, inputElement);
      wrapper.appendChild(inputElement);
      wrapper.appendChild(button);
    }
    
    // Wait for next frame to ensure DOM is ready
    requestAnimationFrame(() => {
      // Force browser reflow
      wrapper.offsetHeight;
      
      // Add loaded class to trigger transitions
      wrapper.classList.add('loaded');
      
      // Update button visibility if enabled
      if (window.velocityState?.isEnabled) {
        button.classList.add('visible');
      }
    });
    inputElement.addEventListener('input', async() => {
  
      clearTimeout(typingTimer);
    typingTimer = setTimeout(() => {
      const text = inputElement.value || inputElement.textContent;
      // Handle input after delay
    }, TYPING_INTERVAL);
      const text = inputElement.value || inputElement.textContent || '';
      const storage = await chrome.storage.local.get(['userName']);

      if (text.length >= CHAR_THRESHOLD_MESSAGE && !helpMessageVisible) {
        const buttonRect = button.getBoundingClientRect();
        if (window.velocityState.platformInfo?.platform != 'claude') {

          popup.style.left = `${buttonRect.left + buttonRect.width/2}px`;
          popup.style.bottom = `${window.innerHeight - buttonRect.top + 10}px`;
        }  
        else{
        const position = calculatePopupPosition(button, popup);
        popup.classList.remove('top', 'bottom');
        popup.classList.add(position);
        }
        if (!settingsSection.classList.contains('show')) {
          messageEl.textContent = `Hey, ${storage.userName} ,I'm here to assist! Click me once you're done typing.`;
          popup.classList.add('show');
          messageEl.style.display = 'block';
        }
      }
    });
    
      
    
   
    // Add visibility based on state
    if (window.velocityState?.isEnabled && platformInfo?.isSupported) {
      button.classList.add('visible');
    }
    // Handle resizing
    const resizeObserver = new ResizeObserver(() => {
      const styles = window.getComputedStyle(inputElement);
      //wrapper.style.width = styles.width;
      wrapper.style.height = 'auto';
      wrapper.style.height = `${inputElement.scrollHeight}px`;
  
    });
    resizeObserver.observe(inputElement);
   
    // First add the popup styles
  const popupStyles = document.createElement('style');
  popupStyles.textContent = `
      .velocity-popup {
    position: fixed !important;
    background: white !important;
    color: #1a1a1a !important;
    padding: 12px 16px !important;
    border-radius: 12px !important;
    font-size: 14px !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
    border: 1px solid rgba(0, 0, 0, 0.1) !important;
    z-index: 9999999 !important;
    width: 275px !important;
    opacity: 0 !important;
    pointer-events: auto !important;
    transition: all 0.2s ease !important;
    visibility: hidden !important;
  }

  .velocity-popup.show {
    opacity: 1 !important;
    pointer-events: auto !important;
    visibility: visible !important;
  }



  

  
  /* Prevent hover conflicts */
  .velocity-enhance-button[data-showing-popup="true"] {
    pointer-events: none !important;
  }

  /* Input styles */
  .velocity-wrapper textarea,
  .velocity-wrapper [contenteditable="true"] {
    width: 100% !important;
    padding-right: 50px !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    background: transparent !important;
  }
  
    .velocity-message {
      margin-bottom: 12px !important;
      font-size:14px;
    }

  
    .settings-section {
      display: none !important;
    }
  
    .settings-section.show {
      display: block !important;
    }
  
      .velocity-style-buttons {
  display: grid !important;
  grid-template-columns: auto auto !important;
  justify-content: start !important;
  gap: 12px !important;
}


    .velocity-style-button:hover {
      background: #E0F2FE !important;
    }
  
    .velocity-style-button.active {
      background: #E0F2FE !important;
      border: 1px solid #3B82F6 !important;
    }

    
  
    .velocity-toggle-container {
      display: flex !important;
      align-items: center !important;
      justify-content: space-between !important;
      background: #F3F4F6 !important;
      padding: 12px !important;
      border-radius: 8px !important;
    }
  
    .velocity-toggle-switch {
      position: relative !important;
      display: inline-block !important;
      width: 44px !important;
      height: 24px !important;
    }
  
    .velocity-toggle-switch input {
      opacity: 0 !important;
      width: 0 !important;
      height: 0 !important;
    }
  
    .velocity-toggle-slider {
      position: absolute !important;
      cursor: pointer !important;
      top: 0 !important;
      left: 0 !important;
      right: 0 !important;
      bottom: 0 !important;
      background-color: #E5E7EB !important;
      transition: .4s !important;
      border-radius: 24px !important;
    }
  
    .velocity-toggle-slider:before {
      position: absolute !important;
      content: "" !important;
      height: 20px !important;
      width: 20px !important;
      left: 2px !important;
      bottom: 2px !important;
      background-color: white !important;
      transition: .4s !important;
      border-radius: 50% !important;
    }
  
    .velocity-toggle-switch input:checked + .velocity-toggle-slider {
      background-color: #3B82F6 !important;
    }
  
    .velocity-toggle-switch input:checked + .velocity-toggle-slider:before {
      transform: translateX(20px) !important;
    }
        .velocity-enhance-button.loading,
  .velocity-enhance-button.loading:hover {
    pointer-events: none !important;
    cursor: not-allowed !important;
    opacity: 0.5 !important;
  }

  `;
  document.head.appendChild(popupStyles);
  
  // Create the popup structure
  // const popup = document.createElement('div');
  // popup.className = 'velocity-popup';
  let userName = 'there'; // Default fallback
  
  let typingTimer;
  const TYPING_INTERVAL = 1000; // 1 second
  
  // Show initial message
  popup.classList.add('show');
  
  // Add breathing effect CSS
  const breathingStyles = document.createElement('style');
  breathingStyles.textContent = `
    @keyframes breathe {
      0% { transform: scale(1); }
      50% { transform:  scale(1.1); }
      100% { transform:  scale(1); }
    }
    
    .velocity-enhance-button.breathing {
      animation: breathe 2s infinite ease-in-out !important;
    }
  `;
  document.head.appendChild(breathingStyles);
  
  try {
    const authState = await checkAuthState();
    if (authState?.userName) {
      userName = authState.userName;
    } else {
      const storage = await chrome.storage.local.get(['userName']);
      if (storage.userName && storage.userName !== 'undefined' && storage.userName !== 'null') {
        userName = storage.userName;
      }
    }
  } catch (error) {
    console.error('Error getting username:', error);
  }
  const storage = await chrome.storage.local.get(['userName']);
  // Create message element
  messageEl.textContent = `Hey ${storage.userName}, I am Velocity. Your personal magician!`;
  popup.appendChild(messageEl);
  
  // Create settings section
  const settingsSection = document.createElement('div');
  settingsSection.className = 'settings-section';
  
  // Create style buttons container
  const styleButtonsContainer = document.createElement('div');
  styleButtonsContainer.className = 'velocity-style-buttons';
  // Replace the existing button styles with:
const buttonStyles = document.createElement('style');
buttonStyles.textContent = `
  .velocity-enhance-button {
    position: absolute !important;
    bottom: 8px !important;  // Changed from top positioning
    right: 12px !important;
    width: 40px !important;
    height: 40px !important;
    padding: 8px !important;
    background: white !important;
    border: none !important;
    border-radius: 50% !important;
    cursor: pointer !important;
    z-index: 999999 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    opacity: 0 !important;
    transition: all 0.2s ease !important;
    pointer-events: auto !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
  }

  .velocity-enhance-button:hover {
    transform: scale(1.05) !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
  }

   .velocity-enhance-button.visible {
    opacity: 1 !important;
    pointer-events: auto !important;
  }

  .velocity-enhance-button img {
    width: 24px !important;
    height: 24px !important;
    transition: transform 0.2s ease !important;
    border-radius: 50% !important;
  }

  @keyframes velocity-breathe {
    0%, 100% { transform:  scale(1); }
    50% { transform:  scale(1.1); }
  }

  .velocity-enhance-button.breathing {
    animation: velocity-breathe 2s ease-in-out infinite !important;
  }

  .velocity-enhance-button.spin {
    animation: velocity-spin 1s linear infinite !important;
  }

  @keyframes velocity-spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

document.head.appendChild(buttonStyles);

function handleButtonAndPopupInteractions(button, popup, messageEl, settingsSection, inputElement) {
  let hideTimeout;
  const HIDE_DELAY = 300;

  function updateButtonAnimations(button, inputElement) {
    const hasContent = (inputElement.value || inputElement.textContent || '').trim().length > 0;
    button.classList.remove('breathing', 'spin');
    if (hasContent && !button.matches(':hover')) {
      button.classList.add('breathing');
    }
  }
  

  function hidePopup() {
    popup.classList.remove('show');
    settingsSection.classList.remove('show');
    messageEl.style.display = 'block';
  }

  function showPopup() {
    if (button.classList.contains('loading')) return;

    const buttonRect = button.getBoundingClientRect();
    popup.style.left = `${buttonRect.left + buttonRect.width/2}px`;
    popup.style.bottom = `${window.innerHeight - buttonRect.top + 10}px`;
    popup.classList.add('show');
  }

  // Button interactions
  button.addEventListener('mouseenter', () => {
    if (button.classList.contains('loading')) return;
    
    clearTimeout(hideTimeout);
    showPopup();
  });

  button.addEventListener('mouseleave', (e) => {
    updateButtonAnimations(button, inputElement);
    
    // Check if mouse moved to popup
    if (!popup.contains(e.relatedTarget)) {
      hideTimeout = setTimeout(hidePopup, HIDE_DELAY);
    }
  });

  // Popup interactions
  popup.addEventListener('mouseenter', () => {
    clearTimeout(hideTimeout);
  });

  popup.addEventListener('mouseleave', (e) => {
    // Check if mouse moved to button
    if (!button.contains(e.relatedTarget)) {
      hideTimeout = setTimeout(hidePopup, HIDE_DELAY);
    }
  });

  return {
    forceHide: hidePopup,
    forceShow: showPopup,
    updatePosition: () => {
      if (popup.classList.contains('show')) {
        const buttonRect = button.getBoundingClientRect();
        popup.style.left = `${buttonRect.left + buttonRect.width/2}px`;
        popup.style.bottom = `${window.innerHeight - buttonRect.top + 10}px`;
      }
    }
  };
}
function updateButtonAnimations(button, inputElement) {
  const hasContent = (inputElement.value || inputElement.textContent || '').trim().length > 0;
  button.classList.remove('breathing', 'spin');
  if (hasContent && !button.matches(':hover')) {
    button.classList.add('breathing');
  }
}

const interactions = handleButtonAndPopupInteractions(
  button, 
  popup, 
  messageEl, 
  settingsSection, 
  inputElement
);

// Add this function to handle button animations

  // Add style buttons
  const styles = [
    {
      name: 'Descriptive',
      description: 'Adds detailed context to enhance clarity and depth',
      imagePath: 'assets/desc.png'
    },
    {
      name: 'Creative',
      description: 'Inspires unique, imaginative, & artistic outputs',
      imagePath: 'assets/cre.png'
    },
    {
      name: 'Professional',
      description: 'Delivers polished, formal, and industry-specific results',
      imagePath: 'assets/pro.png'
    },
    {
      name: 'Concise',
      description: 'Focuses on brevity and clarity, cutting out unnecessary details',
      imagePath: 'assets/conc.png'
    }
  ];

  
  styles.forEach(style => {
    const styleButton = document.createElement('button');
    styleButton.className = 'velocity-style-button';
    styleButton.dataset.style = style.name.toLowerCase();
    
    const gridContainer = document.createElement('div');
    gridContainer.className = 'velocity-style-grid';
    
    const imageContainer = document.createElement('div');
    imageContainer.className = 'velocity-style-image';
    const img = document.createElement('img');
    img.src = chrome.runtime.getURL(style.imagePath);
    img.alt = style.name;
    imageContainer.appendChild(img);
    
    const textContainer = document.createElement('div');
    textContainer.className = 'velocity-style-text';
    
    const titleSpan = document.createElement('span');
    titleSpan.className = 'velocity-style-button-title';
    titleSpan.textContent = style.name;
    
    textContainer.appendChild(titleSpan);
    
    gridContainer.appendChild(imageContainer);
    gridContainer.appendChild(textContainer);
    styleButton.appendChild(gridContainer);
  
    // Update the styles in popupStyles.textContent
    const newStyles = `
       .velocity-style-button {
  padding: 8px 8px !important;
  white-space: nowrap !important;
  width: auto !important;
  background: rgb(255, 255, 255) !important;
  border: 1px solid #E5E7EB !important;
  border-radius: 8px !important;
  cursor: pointer !important;
  width: 100% !important;
  text-align: left !important;
  transition: all 0.2s ease !important;
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
}

.velocity-style-grid {
  display: flex !important;
  align-items: center !important;
  gap: 5px !important;
}

.velocity-style-image {
  width: 24px !important;
  height: 24px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.velocity-style-image img {
  width: 20px !important;
  height: 20px !important;
  object-fit: contain !important;
}

.velocity-style-text {
  display: flex !important;
  align-items: center !important;
}

.velocity-style-button-title {
  font-weight: 500 !important;
  font-size: 14px !important;
  color: #1a1a1a !important;
}




.velocity-style-button:hover {
  background: rgb(255, 255, 255) !important;
  border: 1px solid rgb(2, 123, 199) !important;
}

.velocity-style-button.active {
  background: rgb(240, 249, 255) !important;
  border: 2px solid rgb(2, 132, 199) !important;
}



    `;
  
    // Add the new styles to the existing popupStyles
    if (popupStyles.textContent.includes('.velocity-style-button {')) {
      popupStyles.textContent = popupStyles.textContent.replace(
        /.velocity-style-button {[\s\S]*?}(?=\s*\.velocity-style-button\.active|$)/g,
        newStyles
      );
    } else {
      popupStyles.textContent += newStyles;
    }
  
    // Add event listener...
    styleButton.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      const currentStyle = styleButton.dataset.style;
      const isCurrentlyActive = styleButton.classList.contains('active');
      
      styleButtonsContainer.querySelectorAll('.velocity-style-button').forEach(btn => {
        btn.classList.remove('active');
      });
  
      if (!isCurrentlyActive) {
        styleButton.classList.add('active');
        window.velocityState.styleType = currentStyle;
        hasStyleSelected = true;
        
        const storage = await chrome.storage.local.get(['userName']);
        messageEl.textContent = `Hey ${storage.userName}, press the button below to enhance your prompt!`;
        await chrome.storage.local.set({ selectedStyle: currentStyle });
      } else {
        window.velocityState.styleType = '';
        hasStyleSelected = false;
        
        const storage = await chrome.storage.local.get(['userName']);
        messageEl.textContent = `Hey ${storage.userName}, select a style that best matches your needs`;
        await chrome.storage.local.remove('selectedStyle');
      }
    });
  
    styleButtonsContainer.appendChild(styleButton);
  });
  
  
   
  settingsSection.appendChild(styleButtonsContainer);
  
  // Create toggle container
  const toggleContainer = document.createElement('div');
  toggleContainer.className = 'velocity-toggle-container';
  
  // const toggleLabel = document.createElement('span');
  // toggleLabel.textContent = 'Enable Enhancement';
  
  // const toggleSwitch = document.createElement('label');
  // toggleSwitch.className = 'velocity-toggle-switch';
  
  // const toggleInput = document.createElement('input');
  // toggleInput.type = 'checkbox';
  // toggleInput.checked = window.velocityState.isEnabled;
  
  // const toggleSlider = document.createElement('span');
  // toggleSlider.className = 'velocity-toggle-slider';
  
  //toggleSwitch.appendChild(toggleInput);
  //toggleSwitch.appendChild(toggleSlider);
  //toggleContainer.appendChild(toggleLabel);
  //toggleContainer.appendChild(toggleSwitch);
  // settingsSection.appendChild(toggleContainer);
  
  // Add settings section to popup
  popup.appendChild(settingsSection);
  
  // Add popup to wrapper
  wrapper.appendChild(popup);
  
  // Track settings visibility
  let isSettingsVisible = false;
  inputElement.addEventListener('input', () => updateButtonAnimations(button, inputElement));
button.addEventListener('mouseenter', () => button.classList.remove('breathing'));
button.addEventListener('mouseleave', () => updateButtonAnimations(button, inputElement));
  // Add event listeners
  button.addEventListener('mouseenter', async() => {
    // Clear any existing hide timeout
    clearTimeout(hideTimeout);
    
    const buttonRect = button.getBoundingClientRect();
    // Position the popup relative to the button
    if (window.velocityState.platformInfo?.platform != 'claude') {
      popup.style.left = `${buttonRect.left + buttonRect.width/2}px`;
    popup.style.bottom = `${window.innerHeight - buttonRect.top + 10}px`;
    }
    else{
    const position = calculatePopupPosition(button, popup);
    popup.classList.remove('top', 'bottom');
    popup.classList.add(position);
    }
    const storage = await chrome.storage.local.get(['userName']);
    
  
    // Show appropriate message based on style selection
    messageEl.textContent = hasStyleSelected ? 
      `Hey ${storage.userName}, press the button below to enhance your prompt!` : 
      `Hey ${storage.userName}, select a style that best matches your needs`;
    
    // Show both message and settings
    messageEl.style.display = 'block';
    settingsSection.classList.add('show');
    popup.classList.add('show');
  });
  
  
  
  
  document.addEventListener('mouseover', (e) => {
    clearTimeout(hideTimeout);
    
    // Only hide if mouse is not over button or popup
    if (!button.contains(e.target) && !popup.contains(e.target)) {
      hideTimeout = setTimeout(() => {
        // Double check hover state before hiding
        if (!button.matches(':hover') && !popup.matches(':hover')) {
          popup.classList.remove('show');
          settingsSection.classList.remove('show');
        }
      }, HIDE_DELAY);
    }
  });
  
  // Add popup mouseleave handler
  popup.addEventListener('mouseleave', (e) => {
    // Only hide if not moving to button
    if (!button.matches(':hover')) {
      hideTimeout = setTimeout(() => {
        popup.classList.remove('show');
        settingsSection.classList.remove('show');
        messageEl.style.display = 'block';
      }, HIDE_DELAY);
    }
  });

  button.addEventListener('click', async (e) => {
    e.preventDefault();
    e.stopPropagation();
  
    if (!platformInfo?.isSupported) return;
  
    const selectedText = getSelectedText(inputElement);
    const fullText = inputElement.value || inputElement.textContent || '';
    
    if (!selectedText && !fullText) return;
  
    try {
      showLoading();
      const textToEnhance = selectedText || fullText;
      const enhancedText = await enhancePrompt(textToEnhance);
  
      // Handle different input types
      if (selectedText) {
        if (inputElement.tagName === 'TEXTAREA' || inputElement.tagName === 'INPUT') {
          const selectionStart = inputElement.selectionStart;
          const selectionEnd = inputElement.selectionEnd;
          inputElement.value = fullText.substring(0, selectionStart) + 
                             enhancedText + 
                             fullText.substring(selectionEnd);
          inputElement.selectionStart = selectionStart;
          inputElement.selectionEnd = selectionStart + enhancedText.length;
        } else {
          const selection = window.getSelection();
          if (selection.rangeCount > 0) {
            const range = selection.getRangeAt(0);
            range.deleteContents();
            range.insertNode(document.createTextNode(enhancedText));
          }
        }
      } else {
        if (inputElement.value !== undefined) {
          inputElement.value = enhancedText;
        } else {
          // Handle contenteditable
          inputElement.textContent = enhancedText;
        }
      }
  
      // Trigger input events for all platforms
      const inputEvent = new Event('input', { bubbles: true });
      inputElement.dispatchEvent(inputEvent);
      
      // Additional events for Claude
      if (platformInfo?.platform === 'claude') {
        const changeEvent = new Event('change', { bubbles: true });
        inputElement.dispatchEvent(changeEvent);
        
        // Trigger focus if needed
        inputElement.focus();
        
        // Force Claude's internal update
        if (inputElement.getAttribute('contenteditable') === 'true') {
          const keyEvent = new KeyboardEvent('keyup', {
            bubbles: true,
            key: 'Space',
            keyCode: 32
          });
          inputElement.dispatchEvent(keyEvent);
        }
      }
  
    } catch (error) {
      console.error('Enhancement failed:', error);
      // Show error message in popup
      const messageEl = document.querySelector('.velocity-message');
      if (messageEl) {
        messageEl.textContent = 'Enhancement failed. Please try again.';
        messageEl.style.color = '#ff4444';
        setTimeout(() => {
          messageEl.style.color = '';
        }, 3000);
      }
    } finally {
      hideLoading();
      updateButtonAnimations(button, inputElement);
    }
  });
  
  // Helper function to get selected text
  function getSelectedText(element) {
    if (element.tagName === 'TEXTAREA' || element.tagName === 'INPUT') {
      return element.value.substring(element.selectionStart, element.selectionEnd);
    } else {
      const selection = window.getSelection();
      if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        if (element.contains(range.commonAncestorContainer)) {
          return selection.toString();
        }
      }
    }
    return '';
  }
  
  // Update popup mouseleave:
  // popup.addEventListener('mouseleave', () => {
  //   if (!button.matches(':hover')) {
  //     popup.classList.remove('show');
  //     settingsSection.classList.remove('show');
  //     messageEl.style.display = 'block';
  //   }
  // });
  
  // Handle toggle changes
  toggleInput.addEventListener('change', () => {
    window.velocityState.isEnabled = toggleInput.checked;
    chrome.runtime.sendMessage({
      action: 'toggleEnhanceButton',
      enabled: toggleInput.checked
    });
  });
  // Assemble popup structure
  
  
  
  
   }
  
   function shouldEnhanceInput(input) {
    if (!input || !input.isConnected ||
        input.closest('.velocity-wrapper') ||
        input.dataset.hasEnhanceButton === 'true' ||
        input.parentElement?.querySelector('.velocity-enhance-button')) {
      return false;
    }
  
    const style = window.getComputedStyle(input);
    const isVisible = style.display !== 'none' &&
      style.visibility !== 'hidden' &&
      style.opacity !== '0' &&
      input.offsetParent !== null;
  
    const isRunwayEditor = input.getAttribute('data-lexical-editor') === 'true';
    const isDiscordInput = input.classList.contains('slateTextArea_e52116') ||
      (input.getAttribute('role') === 'textbox' && input.classList.toString().includes('slateTextArea_'));
    const isChatGPTInput = input.matches('#prompt-textarea') || 
      (input.getAttribute('contenteditable') === 'true' && input.classList.contains('ProseMirror'));
      (input.tagName === 'TEXTAREA' && input.classList.contains('resize-none') && 
     input.classList.contains('overflow-hidden') && input.classList.contains('border-0') && 
     input.classList.contains('bg-transparent'));

    if (window.velocityState.platformInfo?.platform === 'discord' && isDiscordInput) {
      return isVisible;
    }
  
    return isVisible && !input.disabled && (
      input.tagName === 'TEXTAREA' ||
      input.tagName === 'INPUT' ||
      input.getAttribute('contenteditable') === 'true' ||
      isRunwayEditor ||
      isChatGPTInput
    );
  }
  
  function setupInitialTextareaHeight(textarea) {
    if (window.velocityState.platformInfo?.platform === 'chatgpt') {
      requestAnimationFrame(() => {
        autoResizeTextarea(textarea);
      });
    }
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
        const existingWrapper = input.closest('.velocity-wrapper');
        if (!existingWrapper) {
          createEnhanceButton(input);
          //setupInitialTextareaHeight(input);

        } else {
          // Update existing button visibility
          const button = existingWrapper.querySelector('.velocity-enhance-button');
          if (button && window.velocityState?.isEnabled) {
            button.classList.add('visible');
          }
        }
      }
    });
  }
  
  function cleanupEnhanceButtons() {
    // Remove injected styles
    const styleElement = document.querySelector('#velocity-inject-styles');
    if (styleElement) {
      styleElement.remove();
    }
  
    // Remove buttons and restore inputs
    document.querySelectorAll('.velocity-wrapper').forEach(wrapper => {
      const input = wrapper.querySelector('textarea, [contenteditable="true"], [role="textbox"]');
      if (input) {
        input.dataset.hasEnhanceButton = 'false';
        wrapper.parentNode.insertBefore(input, wrapper);
        wrapper.remove();
      }
    });
  }
  

            
  function setupEditObserver() {
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.addedNodes) {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === 1) { // Element node
            const editTextarea = node.querySelector('textarea.resize-none.overflow-hidden.border-0.bg-transparent');
            if (editTextarea && !editTextarea.closest('.velocity-wrapper')) {
              createEnhanceButton(editTextarea);
            }
          }
        });
      }
    });
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
}
  (async function init() {
    try {
      const platformInfo = await detectPlatform();
      if (!platformInfo.isSupported) {
        console.log('Unsupported platform, stopping initialization');
        return;
      }
    
      const currentState = window.velocityState || {};
      window.velocityState = {
        ...currentState,
        isEnabled: false,
        platformInfo: platformInfo,
        styleType: ''
      };
    
      if (platformInfo.isSupported) {
        await injectStyles();
        //createWelcomeMessage(); // Add this        
        //setupObservers();
        //setupEditObserver();
        findAndEnhanceInputs();
      }
    } catch (error) {
      console.error('Initialization error:', error);
    }
  })();
  
  
  })();