let userId= "";
let token = "";
let selectedStyle = null; // Default value
let selectedPlatform = null;   // Default value
let hasText = false;  // Track if text exists
let currentLength;
let isShowingResponses = false;
const MIXPANEL_TOKEN = '48a67766d0bb1b3399a4f956da9c52da';
let creditRates = {
  basic_prompt: 2,
  style_prompt: 3,
  platform: 2
};
function initMixpanel() {
  try {
      if (typeof mixpanel !== 'undefined') {
          mixpanel.init(MIXPANEL_TOKEN, {
              debug: true,
              track_pageview: true
          });
          
          // Track extension open
          trackEvent('Extension Opened');
          
          console.log('Mixpanel initialized successfully');
      } else {
          console.error('Mixpanel not loaded');
      }
  } catch (error) {
      console.error('Error initializing Mixpanel:', error);
  }
}
async function fetchCreditRates() {
  try {
    const response = await fetch(`https://thinkvelocity.in/api/api/credit/credits`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
      const responseData = await response.json();
      responseData.data.forEach(item => {
        creditRates[item.feature] = item.credits;
    });
    updateCalculatedCredits();
  } catch (error) {
      console.error('Error fetching credit rates:', error);
  }
}
function updateCalculatedCredits() {
  console.log("update credit display called");
  let totalCredits = 0;
  const selectedPlatform = getSelectedPlatform();
  const selectedStyle = getSelectedStyle();
  console.log("selected platform:"+selectedPlatform + "selected style:"+selectedStyle);
  // Add basic prompt cost always
  if(currentLength>0){
  totalCredits += creditRates.basic_prompt || 0;
  }
  // Add style cost if selected
  if (selectedStyle && selectedStyle !== 'default') {
      totalCredits += creditRates.style_prompt || 0;
  }

  // Add platform cost if selected
  if (selectedPlatform && selectedPlatform !== 'default') {
      totalCredits += creditRates.platform || 0;
  }

  // Update the display in the button
  const creditDisplay = document.querySelector('#creditAmount');
  if (creditDisplay) {
      creditDisplay.textContent = totalCredits;
  }
}



function trackEvent(eventName, properties = {}) {
  try {
      if (typeof mixpanel !== 'undefined') {
          mixpanel.track(eventName, {
              ...properties,
              timestamp: new Date().toISOString()
          });
          console.log('Event tracked:', eventName, properties);
      } else {
          console.error('Mixpanel not available for tracking');
      }
  } catch (error) {
      console.error('Error tracking event:', error);
  }
}

//import ExtensionAnalytics from './analytics';

// mixpanel.init('48a67766d0bb1b3399a4f956da9c52da', {
//   debug: true,
//   track_pageview: true
// });

async function checkFeatureAccess(featureId) {
  try {
    const userId = localStorage.getItem('userId');
    const response = await fetch(`https://thinkvelocity.in/api/api/credit/credits/${featureId}/access`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ userId })
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error checking feature access:', error);
    throw error;
  }
}
function showTextBoxError(message)
{ 
  
  const promptInput = document.getElementById('promptInput');
  const errorContainer = document.querySelector('.error-message-container');


  promptInput.style.border = '0.2px solid red';

  // Add error message
  if (errorContainer) {
    errorContainer.textContent = `${message}`;
    errorContainer.style.color = 'red';
  } else {
    // Create error container if it doesn't exist
    const newErrorContainer = document.createElement('div');
    newErrorContainer.className = 'error-message-container text-red-500 text-sm mt-1';
    newErrorContainer.textContent = 'Please enter a prompt text';
    promptInput.parentNode.appendChild(newErrorContainer);
  }
  setTimeout(() => {
    promptInput.style.border = '';
    errorContainer.textContent = '';
    //errorContainer.remove();
  }, 3000);
  //return;
}
function showTokenError() {
  const editButton = document.getElementById('editButton');
  
  // Add only red border while preserving original shape
  editButton.style.border = '1px solid #FF0000';
  // Don't modify any other styles of the button
  
  // Check if error message already exists and remove it
  const existingError = document.getElementById('tokenErrorMsg');
  if (existingError) {
    existingError.remove();
  }
  
  // Create new error message
  const tokenErrorMsg = document.createElement('div');
  tokenErrorMsg.id = 'tokenErrorMsg';
  
  // Style the container
  tokenErrorMsg.style.cssText = `
    color: #FF0000;
    font-size: 9px;
    margin-top: 8px;
    width: 100%;
    position: absolute;
    top: 100%;
    left: 0;
    text-align: center;
    font-weight: 500;
  `;
  
  // Create the error message with a linked "top up"
  tokenErrorMsg.innerHTML = `
    Not enough credits. Please 
    <a href="https://thinkvelocity.in/profile" 
       style="color: #FF0000; text-decoration: underline; cursor: pointer;"
       target="_blank">
      top up
    </a>.
  `;
  
  // Insert after editButton
  editButton.parentElement.style.position = 'relative';
  editButton.parentElement.appendChild(tokenErrorMsg);
  
  // Remove styling after 5 seconds
  setTimeout(() => {
    editButton.style.border = '';
    tokenErrorMsg.remove();
  }, 5000);
}
function showLoginError() {
  const signupButton = document.getElementById('signupButton');
  signupButton.style.border = '1px solid #FF0000';
  
  const existingError = document.getElementById('loginErrorMsg');
  if (existingError) existingError.remove();
  
  const loginErrorMsg = document.createElement('span');
  loginErrorMsg.id = 'loginErrorMsg';
  loginErrorMsg.style.cssText = `
    color: #FF0000;
    font-size: 9px;
    margin-top: 8px;
    position: absolute;
    top: 100%;
    left: -40px; /* Added left margin */
    font-weight: 500;
    white-space: nowrap;
  `;
  
  loginErrorMsg.innerHTML = 'Please <a href="https://thinkvelocity.in/login" style="color: #FF0000; text-decoration: underline; cursor: pointer;" target="_blank">login</a> to continue.';
  
  signupButton.parentElement.style.position = 'relative';
  signupButton.parentElement.appendChild(loginErrorMsg);
  
  setTimeout(() => {
    signupButton.style.border = '';
    loginErrorMsg.remove();
  }, 5000);
 }
function addUnselectCapability() {
  // Style radio handling
  document.querySelectorAll('.button-group input[type="radio"]').forEach(input => {
    const existingHandler = input.onclick;
    input.onclick = async function(e) {
      console.log("style toggled");
      
      if (this.checked && this.dataset.wasChecked === 'true') {
        this.checked = false;
        this.dataset.wasChecked = 'false';
        selectedStyle = null;
        await chrome.storage.local.remove('selectedStyle');
      } else {
        document.querySelectorAll('.button-group input[type="radio"]').forEach(radio => {
          radio.dataset.wasChecked = 'false';
        });
        this.dataset.wasChecked = 'true';
        selectedStyle = this.id;
        await chrome.storage.local.set({ selectedStyle });
      }
      //updateCalculatedCredits();
      // Call updateCreditDisplay after state has been updated
      setTimeout(() => {
        if (typeof updateCalculatedCredits === 'function') {
          updateCalculatedCredits();
          console.log('Credits updated after style change:', selectedStyle);
        } else {
          console.error('updateCreditDisplay is not defined');
        }
      }, 0);
      
      if (existingHandler) existingHandler.call(this, e);
    };
  });

  // Platform radio handling
  document.querySelectorAll('.radio-group input[type="radio"]').forEach(input => {
    const existingHandler = input.onclick;
    input.onclick = async function(e) {
      console.log("platform toggled");
      
      if (this.checked && this.dataset.wasChecked === 'true') {
        this.checked = false;
        this.dataset.wasChecked = 'false';
        selectedPlatform = null;
        await chrome.storage.local.remove('selectedPlatform');
      } else {
        document.querySelectorAll('.radio-group input[type="radio"]').forEach(radio => {
          radio.dataset.wasChecked = 'false';
        });
        this.dataset.wasChecked = 'true';
        selectedPlatform = this.value;
        await chrome.storage.local.set({ selectedPlatform });
      }
      
      // Call updateCreditDisplay after state has been updated
      setTimeout(() => {
        if (typeof updateCalculatedCredits === 'function') {
          updateCalculatedCredits();
          console.log('Credits updated after platform change:', selectedPlatform);
        } else {
          console.error('updateCreditDisplay is not defined');
        }
      }, 0);
      
      if (existingHandler) existingHandler.call(this, e);
      if (typeof updateEnhanceParameters === 'function') updateEnhanceParameters();
    };
  });
}



async function recordFeatureUsage(featureId) {
  try {
    const userId = localStorage.getItem('userId');
    const response = await fetch(`https://thinkvelocity.in/api/api/credit/use/${featureId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ userId })
    });

    const data = await response.json();
    if (!data.success) {
      throw new Error(data.message);
    }
    return data;
  } catch (error) {
    console.error('Error recording feature usage:', error);
    throw error;
  }
}

const style = document.createElement('style');
  style.textContent = `
    #editButton.token-error {
    border: 1px solid #FF0000;
    transition: border-color 0.3s ease;
  }
  
  #tokenErrorMsg {
    opacity: 1;
    transition: opacity 0.3s ease;
  }
  
  #tokenErrorMsg.hiding {
    opacity: 0;
  }

    .responses-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 10px;
    }
    
    .response-container {
        transition: all 0.3s ease;
    }
    
    .response-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .copy-button {
        opacity: 0.7;
        transition: opacity 0.3s ease;
    }
    
    .copy-button:hover {
        opacity: 1;
    }

    .textarea-wrapper {
    position: relative !important;
    display: inline-block !important;
    width: 100% !important;
  }

  .extension-button {
    position: absolute !important;
    bottom: 5px !important;
    right: 5px !important;
    padding: 5px 10px !important;
    background: linear-gradient(180deg, #000000 0%, #008ACB 100%) !important;
    color: white !important;
    border: 1px solid #444444 !important;
    border-radius: 5px !important;
    cursor: pointer !important;
    z-index: 999999 !important;
    opacity: 0 !important;
    transition: opacity 0.3s ease !important;
    pointer-events: none !important;
  }

  .extension-button.enabled {
    opacity: 1 !important;
    pointer-events: auto !important;
  }

  .extension-button:hover {
    box-shadow: 0 0 10px rgba(0, 138, 203, 0.5) !important;
    transform: translateY(-1px) !important;
  }
    
    .copy-button.copied::after {
        content: 'Copied!';
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        pointer-events: none;
    }
`;
document.head.appendChild(style);

function updateHeaderUI() {
  if (!userId || !token) {
      // User is not logged in
      signupButton.innerHTML = `
          <span><img class="profileicon" src="./assets/profile.png" alt=""></span>
          Sign Up
      `;
      signupButton.classList.add('not-logged-in');
      
      // Add click event listener for login redirect
      //signupButton.addEventListener('click', navigateToLogin);
      
      // Hide credits button and logout button
      if (editButton) editButton.style.display = 'none';
    
  } else {
      // User is logged in
      // Show logout button
      
      // Remove the login redirect listener
      signupButton.classList.remove('not-logged-in');
      console.log("checking user id:"+userId);
      // Fetch and display user info
      fetch(`https://thinkvelocity.in/api/api/users/profile/${userId}`, {
          method: 'GET',
          headers: {
              'Authorization': `Bearer ${token}`
          }
      })
      .then(response => response.json())
      .then(data => {
        const username = data.data.user.name;
        const displayName = username.length > 6 ? username.slice(0, 6) + '..' : username;
        
        signupButton.innerHTML = `
            <span><img class="profileicon" src="./assets/profile.png" alt=""></span>
            Hi ${displayName}!
        `;
          // Show credits button
          if (editButton) editButton.style.display = 'flex';
      })
      .catch(error => console.error('Error fetching user profile:', error));
  }
}

function getSelectedRadioValue() {
  const selectedRadio = document.querySelector('input[name="option"]:checked');
  console.log('Selected radio value:', selectedRadio?.value); // Debug log
  return selectedRadio ? selectedRadio.value : 'General'; // Provide default value
}
function showError(message) {
  const responseDiv = document.getElementById('response');
  if (!responseDiv) {
    console.log('Creating response div');
    responseDiv = document.createElement('div');
    responseDiv.id = 'response';
    document.body.appendChild(responseDiv);
  }

  const errorDiv = document.createElement('div');
  errorDiv.className = 'error-message rounded-2xl border border-red-500 p-4 mb-4';
  errorDiv.style.cssText = `
    color: white;
    text-align: center;
    width: 100%;
    max-width: 640px;
    margin: 0 auto;
    box-sizing: border-box;
    background: rgba(0, 0, 0, 0.4);
  `;


  
  const errorContent = document.createElement('div');
  errorContent.className = 'flex items-center justify-center gap-2';
  
  const errorIcon = document.createElement('span');
  errorIcon.innerHTML = '⚠️';
  errorIcon.className = 'text-xl';
  
  const errorText = document.createElement('span');
  errorText.textContent = message;
  
  errorContent.appendChild(errorIcon);
  errorContent.appendChild(errorText);
  errorDiv.appendChild(errorContent);
  
  responseDiv.innerHTML = '';
  responseDiv.appendChild(errorDiv);

  setTimeout(() => {
    if (responseDiv.contains(errorDiv)) {
      errorDiv.remove();
    }
  }, 5000);
}
document.addEventListener('DOMContentLoaded', () => {
  // Check current auth state
  chrome.storage.local.get(['userId','token','isAuthenticated', 'userName', 'userEmail'], (data) => {
    if (data.userEmail) {
      // Update UI for logged in state
      document.getElementById('signupButton').textContent = `${data.userName}`;
      // Enable extension features
      //console.log("enable features" + data.token);
      userId = data.userId;
      token = data.token;
      localStorage.setItem('userId',userId);
      localStorage.setItem('token',token);
      // console.log("token:" + token);
      // console.log("user Id:" + userId);
      updateCreditDisplay();
      updateHeaderUI();
      fetchCreditRates();

      //enableFeatures();
    } else {
      // Show login prompt
      document.getElementById('signupButton').textContent = 'Login';
      document.getElementById('signupButton').addEventListener('click', function() {
        // Open your lander URL in a new tab
        chrome.tabs.create({ url: 'https://thinkvelocity.in/login' });
        
        // If you're using Mixpanel, track this event
        trackEvent('Login Button Clicked');
      
    });
      // Disable extension features
      //disableFeatures();
      console.log("disable features");
    }
  });
});
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  //console.log("on popup received message:"+message);
  if (message.type === 'AUTH_STATE_CHANGED') {
    // Update extension UI based on new auth state
    if (message.data.userEmail) {
      document.getElementById('signupButton').textContent = `Logged in as ${message.data.userName}`;
//      enableFeatures();
      console.log("enable features");

    } else {
      document.getElementById('signupButton').textContent = 'Login';
      //disableFeatures();
      console.log("disable features");

    }
  }
});

const velocityUI = {
  loadingStates: new Map(),
  
  createLoader(message = 'Processing your request...') {
    const overlay = document.createElement('div');
    overlay.className = 'velocity-overlay';
    overlay.innerHTML = `
      <div class="velocity-loader">
        <div class="velocity-spinner"></div>
        <div class="velocity-loader-text">${message}</div>
      </div>
    `;
    return overlay;
  },

  async showLoading(key = 'default', message) {
    if (this.loadingStates.has(key)) return;
    
    const loader = this.createLoader(message);
    document.body.appendChild(loader);
    this.loadingStates.set(key, loader);
    
    // Disable interactive elements
    document.querySelectorAll('button, input, textarea').forEach(el => {
      if (!el.disabled) {
        el.dataset.wasEnabled = 'true';
        el.disabled = true;
      }
    });
  },



  hideLoading(key = 'default') {
    const loader = this.loadingStates.get(key);
    if (loader) {
      loader.remove();
      this.loadingStates.delete(key);
      
      // Re-enable interactive elements
      document.querySelectorAll('[data-was-enabled]').forEach(el => {
        el.disabled = false;
        delete el.dataset.wasEnabled;
      });
    }
  }
};

// Enhanced Error Handling
const velocityErrors = {
  types: {
    TOKEN: 'token',
    NETWORK: 'network',
    VALIDATION: 'validation',
    SERVER: 'server'
  },

  createError(type, message, action) {
    const error = document.createElement('div');
    error.className = 'velocity-error';
    error.innerHTML = `
      <svg class="velocity-error-icon" width="20" height="20" viewBox="0 0 20 20">
        <path d="M10 0C4.48 0 0 4.48 0 10s4.48 10 10 10 10-4.48 10-10S15.52 0 10 0zm0 11c-.55 0-1-.45-1-1V6c0-.55.45-1 1-1s1 .45 1 1v4c0 .55-.45 1-1 1zm1 4H9v-2h2v2z" 
              fill="currentColor"/>
      </svg>
      <div class="velocity-error-content">
        <div>${message}</div>
        ${action ? `<button class="velocity-error-action">${action}</button>` : ''}
      </div>
    `;
    return error;
  },

  showError(type, message, duration = 5000) {
    const responseDiv = document.getElementById('response');
    const error = this.createError(type, message);
    
    // Clear existing errors
    responseDiv.querySelectorAll('.velocity-error').forEach(el => el.remove());
    
    responseDiv.prepend(error);
    
    if (duration) {
      setTimeout(() => error.remove(), duration);
    }
    
    return error;
  }
};

// Token Management
const velocityTokens = {
  async checkTokenBalance() {
    const response = await fetch(`https://thinkvelocity.in/api/api/token-types/${userId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    return {
      available: data.data.token_received - data.data.tokens_used,
      total: data.data.token_received
    };
  },

  createTokenAlert() {
    const alert = document.createElement('div');
    alert.className = 'velocity-token-alert';
    alert.innerHTML = `
      <div class="velocity-token-header">
        <span class="velocity-token-title">Out of tokens</span>
      </div>
      <p class="velocity-token-message">
        You've used all your available tokens. Top up to continue generating responses.
      </p>
      <button onclick="velocityTokens.handleTopUp()" class="velocity-token-button">
        Top Up Tokens
      </button>
    `;
    return alert;
  },

  async handleTopUp() {
    // Open token purchase page in new tab
    chrome.tabs.create({ url: 'https://thinkvelocity.in/pricing' });
  }
};

// Response Visibility Management
const velocityResponses = {
  scrollIndicator: null,

  createScrollIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'velocity-scroll-indicator';
    indicator.innerHTML = `
      <div class="velocity-scroll-icon">
        <div class="velocity-scroll-dot"></div>
      </div>
      <span>Scroll to see more</span>
    `;
    return indicator;
  },

  showScrollIndicator(container) {
    if (!this.scrollIndicator) {
      this.scrollIndicator = this.createScrollIndicator();
      container.appendChild(this.scrollIndicator);
      
      // Show indicator when content exceeds viewport
      if (container.scrollHeight > container.clientHeight) {
        this.scrollIndicator.style.opacity = '1';
      }
      
      // Hide indicator on scroll
      container.addEventListener('scroll', () => {
        this.scrollIndicator.style.opacity = '0';
      }, { once: true });
    }
  }
};

async function sendRequest() {
  let promptHistoryId = null;
  let creditsDeducted = false;

  try {
    // Initialize loader and disable interactions
    await velocityUI.showLoading('generate', 'Crafting your enhanced response...');
    
    const promptInput = document.getElementById('promptInput');
    const prompt = promptInput.value.trim();
    const CHAR_LIMIT = 1100;

    // Validate permissions and features
    const valid = await verifyAndRecordFeatures();
    if (!valid) {
      velocityErrors.showError(
        velocityErrors.types.VALIDATION, 
        'Feature access validation failed'
      );
      return;
    }

    // Input validation with enhanced error handling
    if (!prompt) {
      showError(
        'Please enter a prompt text'
      );
      return;
    }

    if (prompt.length > CHAR_LIMIT) {
      trackEvent('Generate Error', {
        error: 'Prompt Too Long',
        promptLength: prompt.length,
        platform: selectedPlatform,
        style: selectedStyle,
        location: "Extension"
      });

      showTextBoxError(
        `Input too long. Please keep your text under ${CHAR_LIMIT} characters.`
      );
      return;
    }

    // Prepare request data
    const response = await fetch('https://thinkvelocity.in/python-api/process', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        prompt,
        style: selectedStyle,
        AIType: selectedPlatform,
        singlePrompt: false
      })
    });

    console.log('Raw server response:', response);

    // Track button click
    trackEvent('Generate Button Clicked', {
      platform: selectedPlatform,
      style: selectedStyle,
      promptLength: prompt.length,
      timestamp: new Date().toISOString()
    });

    
    // Update loader message for API call
    velocityUI.showLoading('generate', 'Processing your request...');
    
    // Make the API request with enhanced error handling
   

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(response.status === 500
        ? `Server error (500): ${errorText}`
        : `Server returned ${response.status}: ${errorText}`);
    }

    // Track successful generation
    trackEvent('Response Generated', {
      location: "Extension"
    });

    const data = await response.json();
    console.log('Parsed response data:', data);
    if (data.error) {
      throw new Error(data.error);
    }

    // Save to history with enhanced error recovery
    try {
      velocityUI.showLoading('history', 'Saving to history...');
      const promptData = await savePromptToHistory(userId, prompt, selectedPlatform);
      if (promptData.success) {
        promptHistoryId = promptData.data.history_id;
        lastSavedPromptId = promptHistoryId;
      }
    } catch (historyError) {
      console.error('Error saving prompt to history:', historyError);
      // Non-blocking error - continue execution
      velocityErrors.showError(
        velocityErrors.types.SERVER,
        'Warning: Failed to save to history',
        3000
      );
    }

    // Process credit deductions with token validation
    velocityUI.showLoading('credits', 'Processing credits...');
    await handleCreditDeductions();
    creditsDeducted = true;

    // Handle the response with scroll indication
    if (data && data.stages?.enhancement?.result) {
      const responseContainer = document.querySelector('.responses-wrapper');
      if (!responseContainer) {
        throw new Error('Response container not found');
      }
      responseContainer.classList.remove('hidden');
      handleParsedResponse(data);
    } else {
      throw new Error('Invalid response structure from server');
    }

    // Cleanup stored prompt
    chrome.storage.local.remove(['promptText']);

  } catch (error) {
    trackEvent('Generate Error', {
      error: error.message,
      platform: selectedPlatform,
      style: selectedStyle,
      location: "Extension"
    });

    console.error('Request failed:', error);
    
    // Enhanced error handling with context
    let errorType = velocityErrors.types.SERVER;
    if (error.message.includes('Network error')) {
      errorType = velocityErrors.types.NETWORK;
    } else if (error.message.includes('token') || error.message.includes('credit')) {
      errorType = velocityErrors.types.TOKEN;
    }

    velocityErrors.showError(errorType, error.message);

    // Check if tokens were deducted but operation failed
    if (creditsDeducted) {
      velocityErrors.showError(
        velocityErrors.types.SERVER,
        'Warning: Credits were deducted but operation failed. Please contact support.',
        0  // Don't auto-dismiss this error
      );
    }

  } finally {
    // Cleanup all loading states
    velocityUI.hideLoading('generate');
    velocityUI.hideLoading('history');
    velocityUI.hideLoading('credits');
    
    // Reset interface with token check
    await resetInterface();
    
    // Check remaining tokens after operation
    const tokenBalance = await velocityTokens.checkTokenBalance();
    if (tokenBalance.available < 1) {
      const responseDiv = document.getElementById('response');
      responseDiv.appendChild(velocityTokens.createTokenAlert());
    }
  }
}



const oldHandler = document.onclick;
document.onclick = null;




function showLoading(message) {
  const responseDiv = document.getElementById('response');
  if (responseDiv) {
    responseDiv.innerHTML = `
      <div class="loading-message">
        ${message}
        <div class="loading-spinner"></div>
      </div>
    `;
    adjustPopupSize();
  }
}
const velocityLoader = {
  container: null,
  loadingMessages: [
    'Processing your request...',
    'Crafting the perfect response...',
    'Analyzing your input...',
    'Almost there...'
  ],

  init() {
    this.container = document.createElement('div');
    this.container.className = 'velocity-loader-container';
    document.body.appendChild(this.container);
  },

  show(message = '') {
    if (!this.container) this.init();
    
    this.container.innerHTML = `
      <div class="velocity-loader-overlay">
        <div class="velocity-loader-content">
          <div class="velocity-loader-spinner"></div>
          <div class="velocity-loader-text">
            ${message || this.loadingMessages[Math.floor(Math.random() * this.loadingMessages.length)]}
          </div>
        </div>
      </div>
    `;
    this.container.style.display = 'flex';
  },

  hide() {
    if (this.container) {
      this.container.style.display = 'none';
    }
  }
};

function adjustPopupSize() {
  const popupHeight = document.body.scrollHeight;
  const popupWidth = document.body.scrollWidth;

  // Check if we're in a Chrome extension context
  if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
    chrome.runtime.sendMessage({
      action: 'adjustSize',
      height: popupHeight,
      width: popupWidth
    }).catch(error => {
      console.log('Size adjustment not available:', error);
    });
  }

  // Fallback: Set size directly if possible
  document.documentElement.style.width = `${popupWidth}px`;
  document.documentElement.style.height = `${popupHeight}px`;
}
// function closeAllDropdowns() {
//   document.querySelectorAll('.dropdown-content').forEach(content => {
//       content.style.display = 'none';
//   });
// }
async function saveResponseToHistory(promptText, originalPromptId, aiType, tokensUsed) {
  console.log("selected ai type:"+aiType);
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

async function savePromptToHistory(userId, promptText, aiType) {
  try {
      const response = await fetch('https://thinkvelocity.in/api/api/history/prompts', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
              user_id: userId,
              prompt_text: promptText,
              ai_type: aiType,
              tokens_used: 0  // Will be updated after generation
          })
      });

      const data = await response.json();
      if (!data.success) {
          console.error('Failed to save prompt:', data.message);
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
      const response = await fetch(`https://thinkvelocity.in/api/api/history/prompts/${promptId}`, {
          method: 'PATCH',
          headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
              tokens_used: tokensUsed
          })
      });

      const data = await response.json();
      if (!data.success) {
          console.error('Failed to update tokens:', data.message);
          throw new Error(data.message);
      }

      return data;
  } catch (error) {
      console.error('Error updating prompt tokens:', error);
      throw error;
  }
}

function getSelectedCategories() {
  const selectedCategories = {};
  document.querySelectorAll('.category-card').forEach(card => {
    const categoryName = card.querySelector('.category-title').textContent;
    const selectedItem = card.querySelector('.dropdown-card.selected');
    if (selectedItem) {
      selectedCategories[categoryName] = selectedItem.querySelector('.dropdown-card-select').textContent.trim();
    }
  });
  return selectedCategories;
}
function getSelectedStyle() {
  const selectedRadio = document.querySelector('.button-group input[type="radio"]:checked');
  selectedStyle = selectedRadio ? selectedRadio.id : null;
  return selectedStyle;
}

// Modified function to get selected platform that works with existing code
function getSelectedPlatform() {
  const selectedRadio = document.querySelector('.radio-group input[type="radio"]:checked');
  selectedPlatform = selectedRadio ? selectedRadio.value : '';
  return selectedPlatform;
}

document.addEventListener('DOMContentLoaded', function() {
  const darkModeToggle = document.getElementById('darkModeToggle');
  const body = document.body;
  
  // Check for saved dark mode preference
  const darkMode = localStorage.getItem('darkMode') === 'true';
  
  // Apply saved preference
  if (darkMode) {
      body.classList.add('dark-mode');
      darkModeToggle.querySelector('img').src = './assets/sun.png'; // You'll need a sun icon
  }
  
  darkModeToggle.addEventListener('click', () => {
      body.classList.toggle('dark-mode');
      const isDarkMode = body.classList.contains('dark-mode');
      localStorage.setItem('darkMode', isDarkMode);
      
      // Toggle icon between sun and moon
      const icon = darkModeToggle.querySelector('img');
      icon.src = isDarkMode ? './assets/sun.png' : './assets/moon.png';
  });
});

// function handleParsedResponse(parsedResponse) {
//   const responsesContainer = document.getElementById('responsesContainer');
//   const responsesTrack = responsesContainer.querySelector('.responses-track');
  
//   // Clear previous responses
//   responsesTrack.innerHTML = '';
  
//   // Show the responses container
//   responsesContainer.classList.remove('hidden');
  
//   try {
//       let prompts;
//       if (typeof parsedResponse === 'string') {
//           prompts = [{ prompt: parsedResponse }];
//       } else if (parsedResponse.prompts) {
//           prompts = parsedResponse.prompts;
//       } else if (Array.isArray(parsedResponse)) {
//           prompts = parsedResponse;
//       } else {
//           prompts = [{ prompt: String(parsedResponse) }];
//       }

//       prompts.forEach((promptObj) => {
//           const responseItem = document.createElement('div');
//           responseItem.className = 'response-item';
          
//           const content = document.createElement('div');
//           content.className = 'response-content';
//           content.textContent = typeof promptObj === 'string' ? promptObj : promptObj.prompt;
          
//           const copyButton = document.createElement('button');
//           copyButton.className = 'copy-button';
//           copyButton.innerHTML = `
//               <img src="./assets/copy 1.png" alt="Copy" class="w-5 h-5">
//               <span>Copy</span>
//           `;
          
//           copyButton.addEventListener('click', async () => {
//               const textToCopy = content.textContent;
//               await navigator.clipboard.writeText(textToCopy);
              
//               copyButton.classList.add('copied');
//               setTimeout(() => copyButton.classList.remove('copied'), 2000);
//           });
          
//           responseItem.appendChild(content);
//           responseItem.appendChild(copyButton);
//           responsesTrack.appendChild(responseItem);
//       });
//   } catch (error) {
//       console.error('Error handling response:', error);
//       showError('Error: Could not process the response from the server.');
//   }
// }
// function toggleEnhanceButton(enabled) {
//   chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
//     chrome.tabs.sendMessage(tabs[0].id, {
//       action: 'toggleEnhanceButton',
//       enabled: enabled
//     });
//   });
// }


// In popup.js
// function updateTabsWithState(isEnabled) {
//   chrome.tabs.query({}, (tabs) => {
//     tabs.forEach(tab => {
//       // First try to inject the content script if it's not already there
//       chrome.scripting.executeScript({
//         target: { tabId: tab.id },
//         files: ['content-script.js']
//       }).then(() => {
//         // After ensuring the content script is there, send the message
//         return chrome.tabs.sendMessage(tab.id, {
//           action: 'toggleEnhanceButton',
//           enabled: isEnabled
//         });
//       }).catch(err => {
//         console.log(`Could not update tab ${tab.id}:`, err);
//       });
//     });
//   });
// }
// function handleParsedResponse(parsedResponse) {
//   const mainContent = document.getElementById('mainContent');
//   const responsesWrapper = document.getElementById('responsesWrapper');
//   const responsesGrid = responsesWrapper.querySelector('.responses-grid');

//   // Clear previous responses
//   responsesGrid.innerHTML = '';

//   try {
//     const prompts = Array.isArray(parsedResponse) ? parsedResponse : 
//                     typeof parsedResponse === 'string' ? [{ prompt: parsedResponse }] : 
//                     parsedResponse.prompts || [{ prompt: String(parsedResponse) }];

//     // Hide main content
//     mainContent.classList.add('hidden');
    
//     // Show responses
//     responsesWrapper.classList.remove('hidden');
//     setTimeout(() => responsesWrapper.classList.add('visible'), 50);
    
//     prompts.forEach((promptObj, index) => {
//       const responseCard = createResponseCard(promptObj, index);
//       responsesGrid.appendChild(responseCard);
//     });

//     isShowingResponses = true;
    
//   } catch (error) {
//     console.error('Error handling response:', error);
//     showError('Failed to process response');
//   }
// }

// function handleParsedResponse(parsedResponse) {
//   const mainContent = document.getElementById('mainContent');
//   const responsesWrapper = document.getElementById('responsesWrapper');
//   const responsesGrid = responsesWrapper.querySelector('.responses-grid');

//   // Clear previous responses
//   responsesGrid.innerHTML = '';

//   try {
//     const prompts = Array.isArray(parsedResponse) ? parsedResponse : 
//                     typeof parsedResponse === 'string' ? [{ prompt: parsedResponse }] : 
//                     parsedResponse.prompts || [{ prompt: String(parsedResponse) }];

//     // First, show the responses wrapper but keep it invisible
//     responsesWrapper.style.display = 'block';
    
//     // Hide main content with transition
//     mainContent.classList.add('hidden');
    
//     // Add responses with animation delay
//     prompts.forEach((promptObj, index) => {
//       const card = createResponseCard(promptObj);
//       card.style.animationDelay = `${index * 100}ms`;
//       responsesGrid.appendChild(card);
//     });

//     // Trigger visibility transition after a short delay
//     setTimeout(() => {
//       responsesWrapper.classList.add('visible');
//     }, 50);

//     isShowingResponses = true;

//   } catch (error) {
//     console.error('Error handling response:', error);
//     showError('Failed to process response');
//   }
// }

const ResponseDebugManager = {
  debugMode: true,
  stateLog: [],

  logState(action, state) {
    if (this.debugMode) {
      console.log(`[Response State]: ${action}`, state);
      this.stateLog.push({ action, state, timestamp: Date.now() });
    }
  },

  // Add visual feedback during transitions
  addLoadingIndicator() {
    const wrapper = document.getElementById('responsesWrapper');
    if (!wrapper) {
      console.error('[Response Debug]: Responses wrapper not found');
      return;
    }
    
    wrapper.insertAdjacentHTML('afterbegin', `
      <div class="response-loading">
        <div class="loading-spinner"></div>
        <div>Processing responses...</div>
      </div>
    `);
  },

  removeLoadingIndicator() {
    const loading = document.querySelector('.response-loading');
    loading?.remove();
  },

  // Check DOM structure integrity
  validateStructure() {
    const results = {
      mainContent: !!document.getElementById('mainContent'),
      responsesWrapper: !!document.getElementById('responsesWrapper'),
      responsesGrid: !!document.querySelector('.responses-grid'),
      structureValid: false
    };
    
    results.structureValid = Object.values(results).every(Boolean);
    this.logState('Structure Validation', results);
    return results;
  },

  // Monitor visibility states
  monitorVisibilityTransition(element, className) {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
          this.logState('Visibility Change', {
            element: element.id,
            classes: element.className,
            display: getComputedStyle(element).display,
            opacity: getComputedStyle(element).opacity
          });
        }
      });
    });

    observer.observe(element, { attributes: true });
    return observer;
  }
};
// function handleParsedResponse(parsedResponse) {
//   console.log('handleParsedResponse input:', parsedResponse);

//   const responsesWrapper = document.getElementById('responsesWrapper');
//   const mainContent = document.getElementById('mainContent');
//   const responsesGrid = document.querySelector('.responses-grid');

//   if (!responsesWrapper || !mainContent || !responsesGrid) {
//     console.error('DOM elements check:', {
//       responsesWrapper: !!responsesWrapper,
//       mainContent: !!mainContent,
//       responsesGrid: !!responsesGrid
//     });
//     return;
//   }

//   responsesGrid.innerHTML = '';

//   try {
//     // Handle server response structure
//     const response = typeof parsedResponse === 'string' ? 
//       JSON.parse(parsedResponse) : parsedResponse;
      
//     const prompts = response.stages?.enhancement?.result?.prompts || [];
    
//     if (!prompts.length) {
//       throw new Error('No prompts received from server');
//     }

//     prompts.forEach((promptObj, index) => {
//       const responseElement = createResponseElement(promptObj);
//       if (responseElement) {
//         responseElement.style.animationDelay = `${index * 100}ms`;
//         responsesGrid.appendChild(responseElement);
//       }
//     });

//     // Show responses wrapper
//     mainContent.classList.add('hidden');
//     responsesWrapper.classList.remove('hidden');
    
//     setTimeout(() => {
//       responsesWrapper.classList.add('visible');
//     }, 50);

//   } catch (error) {
//     console.error('Error displaying responses:', error);
//     showError('Failed to display responses');
//   }
// }

function handleParsedResponse(parsedResponse) {
  const responsesWrapper = document.getElementById('responsesWrapper');
  const mainContent = document.getElementById('mainContent');
  const responsesGrid = document.querySelector('.responses-grid');

  responsesGrid.innerHTML = '';

  try {
    const response = parsedResponse.stages?.enhancement?.result?.result || {};
    const prompts = response.prompts || [];
    
    if (!prompts.length) {
      throw new Error('No prompts received from server');
    }

    prompts.forEach((promptObj, index) => {
      const responseElement = createResponseElement(promptObj);
      if (responseElement) {
        responseElement.style.animationDelay = `${index * 100}ms`;
        responsesGrid.appendChild(responseElement);
      }
    });

    mainContent.classList.add('hidden');
    responsesWrapper.classList.remove('hidden');
    
    setTimeout(() => {
      responsesWrapper.classList.add('visible');
    }, 50);

  } catch (error) {
    console.error('Error displaying responses:', error);
    showError('Failed to display responses');
  }
}

function createResponseElement(promptObj) {
  const card = document.createElement('div');
  card.className = 'response-card';
  
  const content = document.createElement('div');
  content.className = 'response-content';
  content.textContent = promptObj.prompt || 'No response available';
  
  const copyButton = document.createElement('button');
  copyButton.className = 'copy-button';
  copyButton.innerHTML = '<span>Copy</span>';
  
  copyButton.addEventListener('click', async () => {
    try {
      await saveResponseToHistory(content.textContent, lastSavedPromptId, getSelectedPlatform());
      await navigator.clipboard.writeText(content.textContent);
      copyButton.classList.add('copied');
      copyButton.querySelector('span').textContent = 'Copied!';
      
      setTimeout(() => {
        copyButton.classList.remove('copied');
        copyButton.querySelector('span').textContent = 'Copy';
      }, 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  });
  
  card.appendChild(content);
  card.appendChild(copyButton);
  return card;
}

// function handleParsedResponse(parsedResponse) {
//   ResponseDebugManager.logState('Response Received', { responseType: typeof parsedResponse });
  
//   const structureCheck = ResponseDebugManager.validateStructure();
//   if (!structureCheck.structureValid) {
//     console.error('[Response Debug]: Invalid DOM structure', structureCheck);
//     return;
//   }

//   const responsesWrapper = document.getElementById('responsesWrapper');
//   const mainContent = document.getElementById('mainContent');
  
//   // Monitor state transitions
//   const visibilityObserver = ResponseDebugManager.monitorVisibilityTransition(responsesWrapper, 'visible');
  
//   try {
//     ResponseDebugManager.addLoadingIndicator();

//     // Force FOUC prevention
//     responsesWrapper.style.display = 'none';
//     responsesWrapper.style.opacity = '0';
//     void responsesWrapper.offsetHeight; // Force reflow

//     // Ensure clean state
//     responsesWrapper.classList.remove('visible', 'hidden');
//     mainContent.classList.remove('hidden');

//     // Sequence the transition
//     requestAnimationFrame(() => {
//       responsesWrapper.style.display = 'block';
      
//       requestAnimationFrame(() => {
//         mainContent.classList.add('hidden');
        
//         setTimeout(() => {
//           responsesWrapper.style.opacity = '1';
//           responsesWrapper.classList.add('visible');
//           ResponseDebugManager.removeLoadingIndicator();
          
//           // Clean up observer
//           visibilityObserver.disconnect();
//           ResponseDebugManager.logState('Transition Complete', { 
//             mainContentHidden: mainContent.classList.contains('hidden'),
//             responsesVisible: responsesWrapper.classList.contains('visible')
//           });
//         }, 50);
//       });
//     });

//     // Process responses with error boundary
//     const normalizedResponses = Array.isArray(parsedResponse) ? parsedResponse : [parsedResponse];
//     const responsesGrid = document.querySelector('.responses-grid');
//     responsesGrid.innerHTML = ''; // Clear existing content

//     normalizedResponses.forEach((response, index) => {
//       const responseElement = createResponseElement(response);
//       if (responseElement) {
//         responseElement.style.animationDelay = `${index * 100}ms`;
//         responsesGrid.appendChild(responseElement);
//       }
//     });

//   } catch (error) {
//     console.error('[Response Debug]: Error handling response', error);
//     ResponseDebugManager.logState('Error', { error: error.message });
//     showError('Failed to display responses. Please try again.');
//   }
// }

// function handleParsedResponse(parsedResponse) {
//   console.log('Handle Parsed Response called with:', parsedResponse);
  
//   const responsesWrapper = document.getElementById('responsesWrapper');
//   const mainContent = document.getElementById('mainContent');
//   const responsesGrid = document.querySelector('.responses-grid');

//   try {
//     // Clear existing responses
//     responsesGrid.innerHTML = '';

//     // Normalize responses
//     const normalizedResponses = Array.isArray(parsedResponse) 
//       ? parsedResponse 
//       : [{ prompt: String(parsedResponse) }];

//     console.log('Normalized Responses:', normalizedResponses);

//     // Create and append response elements
//     normalizedResponses.forEach((response, index) => {
//       const responseElement = createResponseElement(response);
//       if (responseElement) {
//         responseElement.style.animationDelay = `${index * 100}ms`;
//         responsesGrid.appendChild(responseElement);
//       }
//     });

//     // Show responses wrapper
//     mainContent.classList.add('hidden');
//     responsesWrapper.classList.remove('hidden');
//     responsesWrapper.classList.add('visible');

//   } catch (error) {
//     console.error('Error in handleParsedResponse:', error);
//   }
// }

// function handleParsedResponse(parsedResponse) {
//   console.log('Handle Parsed Response called with:', parsedResponse);
  
//   const responsesWrapper = document.getElementById('responsesWrapper');
//   const mainContent = document.getElementById('mainContent');
//   const responsesGrid = document.querySelector('.responses-grid');

//   try {
//     // Clear existing responses
//     responsesGrid.innerHTML = '';

//     // Normalize responses
//     const normalizedResponses = Array.isArray(parsedResponse) 
//       ? parsedResponse 
//       : [{ prompt: String(parsedResponse) }];

//     console.log('Normalized Responses:', normalizedResponses);

//     // Create and append response elements
//     normalizedResponses.forEach((response, index) => {
//       const responseElement = createResponseElement(response);
//       if (responseElement) {
//         responseElement.style.animationDelay = `${index * 100}ms`;
//         responsesGrid.appendChild(responseElement);
//       }
//     });

//     // Show responses wrapper
//     mainContent.classList.add('hidden');
//     responsesWrapper.classList.remove('hidden');
    
//     // Use a small timeout to ensure transition
//     setTimeout(() => {
//       responsesWrapper.classList.add('visible');
//     }, 50);

//   } catch (error) {
//     console.error('Error in handleParsedResponse:', error);
//     showError('Failed to display responses');
//   }
// }

// function handleParsedResponse(parsedResponse) {
//   console.log('Full Response:', parsedResponse);
  
//   const responsesWrapper = document.getElementById('responsesWrapper');
//   const mainContent = document.getElementById('mainContent');
//   const responsesGrid = document.querySelector('.responses-grid');

//   try {
//     // Clear existing responses
//     responsesGrid.innerHTML = '';

//     // Extract prompts from the response
//     const prompts = parsedResponse.response?.prompts || [];

//     console.log('Extracted Prompts:', prompts);

//     // Create and append response elements
//     prompts.forEach((promptObj, index) => {
//       const responseElement = createResponseElement(promptObj);
//       if (responseElement) {
//         responseElement.style.animationDelay = `${index * 100}ms`;
//         responsesGrid.appendChild(responseElement);
//       }
//     });

//     // Show responses wrapper
//     mainContent.classList.add('hidden');
//     responsesWrapper.classList.remove('hidden');
    
//     // Use a small timeout to ensure transition
//     setTimeout(() => {
//       responsesWrapper.classList.add('visible');
//     }, 50);

//   } catch (error) {
//     console.error('Error in handleParsedResponse:', error);
//     showError('Failed to display responses');
//   }
// }

// function createResponseElement(promptObj) {
//   const card = document.createElement('div');
//   card.className = 'response-card';
  
//   const content = document.createElement('div');
//   content.className = 'response-content';
//   content.textContent = promptObj.prompt || 'No response available';
  
//   const copyButton = document.createElement('button');
//   copyButton.className = 'copy-button';
//   copyButton.innerHTML = `
//     <img src="./assets/copy.png" alt="Copy" class="copy-icon">
//     <span>Copy</span>
//   `;
  
//   copyButton.addEventListener('click', async () => {
//     try {
//       await navigator.clipboard.writeText(content.textContent);
//       copyButton.classList.add('copied');
//       copyButton.querySelector('span').textContent = 'Copied!';
      
//       setTimeout(() => {
//         copyButton.classList.remove('copied');
//         copyButton.querySelector('span').textContent = 'Copy';
//       }, 2000);
//     } catch (err) {
//       console.error('Failed to copy:', err);
//     }
//   });
  
//   card.appendChild(content);
//   card.appendChild(copyButton);
//   return card;
// }


function createResponseElement(response) {
  const card = document.createElement('div');
  card.className = 'response-card';
  
  const content = document.createElement('div');
  content.className = 'response-content';
  content.textContent = response.prompt || response;
  
  const copyButton = document.createElement('button');
  copyButton.className = 'copy-button';
  copyButton.innerHTML = `
    <span>Copy</span>
  `;
  
  copyButton.addEventListener('click', async () => {
    try {
      saveResponseToHistory(content.textContent, lastSavedPromptId,getSelectedPlatform())
      await navigator.clipboard.writeText(content.textContent);
      copyButton.classList.add('copied');
      copyButton.querySelector('span').textContent = 'Copied!';
      
      setTimeout(() => {
        copyButton.classList.remove('copied');
        copyButton.querySelector('span').textContent = 'Copy';
      }, 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  });
  
  card.appendChild(content);
  card.appendChild(copyButton);
  return card;
}

function createResponseCard(promptObj) {
  const card = document.createElement('div');
  card.className = 'response-card';
  
  const content = document.createElement('div');
  content.className = 'response-content';
  content.textContent = promptObj.prompt;
  
  const copyButton = document.createElement('button');
  copyButton.className = 'copy-button';
  copyButton.innerHTML = `
    <span>Copy</span>
  `;
  
  copyButton.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(promptObj.prompt);
      copyButton.classList.add('copied');
      copyButton.querySelector('span').textContent = 'Copied!';
      
      setTimeout(() => {
        copyButton.classList.remove('copied');
        copyButton.querySelector('span').textContent = 'Copy';
      }, 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  });
  
  card.appendChild(content);
  card.appendChild(copyButton);
  return card;
}

const ResponseManager = {
  transitionDuration: 300, // Match CSS transition duration
  isTransitioning: false,

  async showResponses(parsedResponse) {
    if (this.isTransitioning) return;
    this.isTransitioning = true;

    const mainContent = document.getElementById('mainContent');
    const responsesWrapper = document.getElementById('responsesWrapper');
    const responsesGrid = responsesWrapper.querySelector('.responses-grid');

    try {
      // Clear existing responses
      responsesGrid.innerHTML = '';

      // Process responses
      const prompts = this.normalizeResponseData(parsedResponse);

      // Prepare responses but don't show yet
      const responseElements = prompts.map((promptObj, index) => 
        this.createResponseCard(promptObj, index)
      );

      // Add all responses to grid
      responseElements.forEach(element => responsesGrid.appendChild(element));

      // Begin transition sequence
      await this.transitionToResponses(mainContent, responsesWrapper);

    } catch (error) {
      console.error('Error handling response:', error);
      showError('Failed to process response');
    } finally {
      this.isTransitioning = false;
    }
  },

  normalizeResponseData(parsedResponse) {
    if (typeof parsedResponse === 'string') {
      return [{ prompt: parsedResponse }];
    }
    if (Array.isArray(parsedResponse)) {
      return parsedResponse;
    }
    if (parsedResponse.prompts) {
      return parsedResponse.prompts;
    }
    return [{ prompt: String(parsedResponse) }];
  },

  createResponseCard(promptObj, index) {
    const card = document.createElement('div');
    card.className = 'response-card';
    card.style.animationDelay = `${index * 100}ms`;
    
    const content = document.createElement('div');
    content.className = 'response-content';
    content.textContent = promptObj.prompt;
    
    const copyButton = this.createCopyButton(promptObj.prompt);
    
    card.appendChild(content);
    card.appendChild(copyButton);
    return card;
  },

  createCopyButton(text) {
    const button = document.createElement('button');
    button.className = 'copy-button';
    button.innerHTML = `
      <span>Copy</span>
    `;
    
    button.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(text);
        this.showCopyFeedback(button);
      } catch (err) {
        console.error('Failed to copy:', err);
      }
    });
    
    return button;
  },

  showCopyFeedback(button) {
    button.classList.add('copied');
    button.querySelector('span').textContent = 'Copied!';
    
    setTimeout(() => {
      button.classList.remove('copied');
      button.querySelector('span').textContent = 'Copy';
    }, 2000);
  },

  transitionToResponses(mainContent, responsesWrapper) {
    return new Promise(resolve => {
      // First, ensure responses wrapper is in the DOM but invisible
      responsesWrapper.style.display = 'block';
      
      // Force reflow
      void responsesWrapper.offsetHeight;

      // Hide main content
      mainContent.classList.add('hidden');

      // After a brief delay, show responses
      setTimeout(() => {
        responsesWrapper.classList.add('visible');
        
        // Resolve after transition completes
        setTimeout(resolve, this.transitionDuration);
      }, 50);
    });
  },

  async hideResponses() {
    if (this.isTransitioning) return;
    this.isTransitioning = true;

    const mainContent = document.getElementById('mainContent');
    const responsesWrapper = document.getElementById('responsesWrapper');

    try {
      // Remove visible class first
      responsesWrapper.classList.remove('visible');

      // Wait for transition
      await new Promise(resolve => setTimeout(resolve, this.transitionDuration));

      // Show main content
      mainContent.classList.remove('hidden');

      // Reset responses wrapper
      responsesWrapper.style.display = 'none';
    } finally {
      this.isTransitioning = false;
    }
  }
};

// Update back button handler
// document.addEventListener('DOMContentLoaded', () => {
//   const backButton = document.getElementById('backToInput');
  
//   backButton.addEventListener('click', () => {
//     if (!isShowingResponses) return;
    
//     const mainContent = document.getElementById('mainContent');
//     const responsesWrapper = document.getElementById('responsesWrapper');
    
//     // Remove visible class first
//     responsesWrapper.classList.remove('visible');
    
//     // Wait for transition to complete before hiding
//     setTimeout(() => {
//       mainContent.classList.remove('hidden');
//       responsesWrapper.style.display = 'none';
//     }, 300);
    
//     isShowingResponses = false;
//   });
// });

document.addEventListener('DOMContentLoaded', () => {
  const backButton = document.getElementById('backToInput');
  backButton?.addEventListener('click', () => ResponseManager.hideResponses());
});

function createResponseCard(promptObj, index) {
  const card = document.createElement('div');
  card.className = 'response-card';
  card.style.animationDelay = `${index * 100}ms`;
  
  const content = document.createElement('div');
  content.className = 'response-content';
  content.textContent = promptObj.prompt;
  
  const copyButton = document.createElement('button');
  copyButton.className = 'copy-button';
  copyButton.innerHTML = `
    <span>Copy</span>
  `;
  
  copyButton.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(promptObj.prompt);
      copyButton.classList.add('copied');
      copyButton.querySelector('span').textContent = 'Copied!';
      
      setTimeout(() => {
        copyButton.classList.remove('copied');
        copyButton.querySelector('span').textContent = 'Copy';
      }, 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  });
  
  card.appendChild(content);
  card.appendChild(copyButton);
  return card;
}

// Initialize back button handler
document.addEventListener('DOMContentLoaded', () => {
  const backButton = document.getElementById('backToInput');
  
  backButton.addEventListener('click', () => {
    if (!isShowingResponses) return;
    
    const mainContent = document.getElementById('mainContent');
    const responsesWrapper = document.getElementById('responsesWrapper');
    
    // Hide responses
    responsesWrapper.classList.remove('visible');
    setTimeout(() => {
      responsesWrapper.classList.add('hidden');
      // Show main content
      mainContent.classList.remove('hidden');
    }, 300);
    
    isShowingResponses = false;
  });
});


function initializeRadioGroup() {
  const radioButtons = document.querySelectorAll('.radio-button');
  radioButtons.forEach(button => {
    button.addEventListener('click', async function() {
      const img = this.querySelector('img');
      const imgSrc = img.src.split('/').pop();
      const platform = imgSrc.split('.')[0];
      
      const platformMap = {
        'radiobutton1': 'General',
        'radiobutton2': 'GPT4',
        'radiobutton3': 'Midjourney',
        'radiobutton4': 'Playground',
        'radiobutton5': 'DALLE'
      };
      
      radioButtons.forEach(btn => btn.classList.remove('selected'));
      this.classList.add('selected');
      
      selectedPlatform = platformMap[platform] || 'General';
      chrome.storage.local.set({ selectedPlatform });
      updateEnhanceParameters();
    });
  });
}

// Add this function to handle style selection

function initializeStyleButtons() {
  const styleButtons = document.querySelectorAll('.button-group input[type="radio"]');
  styleButtons.forEach(button => {
    button.addEventListener('click', function() {
      selectedStyle = this.id;
      chrome.storage.local.set({ selectedStyle });
      updateEnhanceParameters();
    });
  });
}



function loadSavedSelections() {
  chrome.storage.local.get(['selectedStyle', 'selectedPlatform'], (result) => {
    // Restore style selection
    if (result.selectedStyle) {
      const styleLabel = document.querySelector(`label[for="${result.selectedStyle}"]`);
      if (styleLabel) {
        const input = document.getElementById(result.selectedStyle);
        if (input) input.checked = true;
        styleLabel.classList.add('selected');
      }
    }

    // Restore platform selection (existing code)
    if (result.selectedPlatform) {
      const platformMap = {
        'General': 'radiobutton1',
        'GPT4': 'radiobutton2',
        'Midjourney': 'radiobutton3',
        'Playground': 'radiobutton4',
        'DALLE': 'radiobutton5'
      };
      
      const buttonId = platformMap[result.selectedPlatform];
      if (buttonId) {
        const radioButton = document.querySelector(`[src*="${buttonId}"]`)?.closest('.radio-button');
        if (radioButton) {
          radioButton.classList.add('selected');
        }
      }
    }
  });
}



// Add this function to update enhance button parameters
function updateEnhanceParameters() {
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    if (!tabs[0]?.id) return;
    chrome.tabs.sendMessage(tabs[0].id, {
      action: 'updateEnhanceParameters',
      platform: getSelectedPlatform(),
      style: selectedStyle,
      enabled: document.getElementById('enhanceToggle').checked
    });
  });
}



async function initializeEnhanceToggle() {
  const toggle = document.getElementById('enhanceToggle');
  if (!toggle) {
    console.error('Toggle element not found');
    return;
  }
  // Load saved state
  chrome.storage.local.get(['enhanceButtonEnabled'], (result) => {
    const isEnabled = result.enhanceButtonEnabled === true;
    toggle.checked = isEnabled;
    // Notify background script to update tabs
    chrome.runtime.sendMessage({
      action: 'updateTabs',
      enabled: isEnabled
    });
    updateEnhanceParameters();
  });
  // Handle toggle changes
  toggle.addEventListener('change', async (event) => {
    if (!userId || !token) {
      event.preventDefault();
      toggle.checked = false;
      showLoginError();
      return;
    }
   
   
        const tokenResponse = await fetch(`https://thinkvelocity.in/api/api/token-types/${userId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      }
    });
    const tokenData = await tokenResponse.json();
    const availableTokens = tokenData.data.token_received - tokenData.data.tokens_used;
    const isEnabled = event.target.checked;
    if(availableTokens>0){
    console.log("called toggele enhanced button:"+isEnabled);
    trackEvent('EnhanceButtonToggle', {
      enabled:isEnabled
    });
  }
  else{
    toggle.checked = false;
    showTokenError();
    //showError('Not enough credits available. Please top up your credits.');
  }
    try {
      // Save state
      await chrome.storage.local.set({'enhanceButtonEnabled': isEnabled });
      updateActiveTab(isEnabled);
      // Update parameters including the new enabled state
      updateEnhanceParameters();
      // Notify background script to update tabs
      chrome.runtime.sendMessage({
        action: 'updateTabs',
        enabled: isEnabled
      });
    } catch (error) {
      console.error('Error handling toggle:', error);
      toggle.checked = !isEnabled; // Revert the toggle if there's an error
    }
  });
}
document.addEventListener('DOMContentLoaded', function() {
  // Add a small delay to ensure Mixpanel is loaded
  setTimeout(() => {
      initMixpanel();
  }, 1000);
});

document.addEventListener('DOMContentLoaded', initializeEnhanceToggle);
function cleanupEventListeners() {
  const existingHandlers = [window.existingClickHandler];
  existingHandlers.forEach(handler => {
    if (handler) {
      document.removeEventListener('click', handler);
    }
  });
}

async function updateActiveTab(isEnabled) {
  console.log(":called");
  chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
    const activeTab = tabs[0];
    console.log("active tab:"+activeTab.id);
    if (!activeTab) return;
    
    // Skip chrome:// URLs and other restricted pages
    // if (activeTab.url.startsWith('chrome://') || 
    //     activeTab.url.startsWith('brave://') || 
    //     activeTab.url.startsWith('chrome-extension://')) {
    //   console.log('Skipping restricted URL:', activeTab.url);
    //   return;
    // }

    try {
      console.log("helooooo");
      // Inject the content script first
      await chrome.scripting.executeScript({
        target: { tabId: activeTab.id },
        files: ['content-script.js']
      });
      console.log("reached here");
      // Then send the toggle message
      const response = await chrome.tabs.sendMessage(activeTab.id, {
        action: 'updateEnhanceParameters',
        platform: getSelectedPlatform(),
        style: selectedStyle,
        enabled: isEnabled
      });
  
      console.log("response receieved:"+response);
    } catch (error) {
      console.error('Error toggling enhance button:', error);
      // Show error in popup UI
      //const errorMessage = document.getElementById('error-message') || createErrorElement();
      showError("Failed to communicate with the page. Please try again.");
      // errorMessage.textContent = 'Failed to communicate with the page. Please try again.';
      // errorMessage.style.display = 'block';
      }
  });
}
// function updateAllTabs(isEnabled) {
//   chrome.tabs.query({}, (tabs) => {
//     tabs.forEach(tab => {
//       chrome.tabs.sendMessage(tab.id, {
//         action: 'toggleEnhanceButton',
//         enabled: isEnabled
//       }).catch(err => {
//         console.log(`Could not send message to tab ${tab.id}:`, err);
//       });
//     });
//   });
// }
function addButtonToTextAreas() {
  const textAreas = document.querySelectorAll('textarea');
  textAreas.forEach(textArea => {
    // Skip if button already exists
    if (textArea.nextElementSibling?.classList.contains('extension-button')) {
      return;
    }

    // Create wrapper if it doesn't exist
    let wrapper = textArea.closest('.textarea-wrapper');
    if (!wrapper) {
      wrapper = document.createElement('div');
      wrapper.className = 'textarea-wrapper';
      textArea.parentNode.insertBefore(wrapper, textArea);
      wrapper.appendChild(textArea);
    }

    // Create enhance button
    const button = document.createElement('button');
    button.textContent = 'Enhance';
    button.className = 'extension-button';
    
    // Check initial state
    chrome.storage.local.get(['enhanceButtonEnabled'], (result) => {
      if (result.enhanceButtonEnabled !== false) {
        button.classList.add('enabled');
      }
    });
    
    wrapper.appendChild(button);
  });
}

document.removeEventListener('click', window.existingClickHandler);

const API_BASE_URL = 'http://127.0.0.1:5000';
document.addEventListener('DOMContentLoaded', function () {
  const sendButton = document.getElementById('sendButton');
  const promptInput = document.getElementById('promptInput');
  chrome.storage.local.get(['promptText'], (result) => {
    if (result.promptText) {
      promptInput.value = result.promptText;
      currentLength = promptInput.value.length;
      updateCharCount(promptInput);
    }
  });

  // Save text on input
  promptInput.addEventListener('input', function() {
    const trimmedPrompt = this.value.trim();
    
    if (trimmedPrompt) {
      this.style.border = '1px solid #E5E7EB';
      errorContainer.textContent = '';
    }

    chrome.storage.local.set({ promptText: this.value });
    updateCharCount(this);
    updateCalculatedCredits();
  });

  const CHAR_LIMIT = 1100;
  //const categoriesContainer = document.getElementById('categories-container');
  const responseDiv = document.getElementById('response');
  //const advancedOptionsButton = document.getElementById('advancedOptionsButton');
  const imageUpload = document.getElementById('imageUpload');
  const imageUploadText = document.querySelector('.image-upload-text');
  
  const iconImage = document.getElementById('generateIcon');
  //const logoutButton = document.querySelector('button[onclick="logout()"]');

  
  // Placeholder image path
  const placeholderImagePath = 'path/to/your/placeholder-image.png';

  const radioGroup = document.querySelector('.radio-group');

  //categoriesContainer.classList.add('hidden2');
  const errorContainer = document.createElement('div');
  errorContainer.className = 'error-message-container';
  errorContainer.style.cssText = `
    color: red;
    font-size: 11px;  // Smaller font size
    padding: 4px 8px;  // Add some padding
    margin-top: 4px;  // Slight margin from the input
    width: 100%;  // Full width
    text-align: left;  // Left-align the text
  `;
    promptInput.parentNode.appendChild(errorContainer);
  promptInput.parentElement.style.position = 'relative';

  // Create character counter
  const charCounter = document.createElement('div');
  charCounter.className = 'char-counter';
  charCounter.style.cssText = `
    position: absolute;
    bottom: -15px;
    right: 12px;
    color: #666;
    font-size: 12px;
    pointer-events: none;
    user-select: none;
    background: transparent;
  `;
  promptInput.parentNode.appendChild(charCounter);

  // Update character count and check limit
  function updateCharCount(input) {
    currentLength = input.value.length;
    charCounter.textContent = `${currentLength}/${CHAR_LIMIT}`;
    
    if (currentLength > CHAR_LIMIT) {
      input.classList.add('border-2', 'border-red-500');
      errorContainer.textContent = 'Input too long. Please keep your text under 1100 characters.';
      charCounter.classList.remove('text-gray-400');
      charCounter.classList.add('text-red-500');
    } else {
      input.classList.remove('border-2', 'border-red-500');
      errorContainer.textContent = '';
      charCounter.classList.remove('text-red-500');
      charCounter.classList.add('text-gray-400');
    }
  }

  // Add input and paste event listeners
  promptInput.addEventListener('input', function() {
    
    updateCharCount(this);
    updateCalculatedCredits();
    // console.log("heyyy");
    // const wasEmpty = !hasText;
    // hasText = this.value.length > 0;
    
    // if (wasEmpty !== hasText) {
    //     updateCalculatedCredits();
    // }
   });

  promptInput.addEventListener('paste', function(e) {
    const pastedText = e.clipboardData.getData('text');
    if ((this.value.length + pastedText.length) > CHAR_LIMIT) {
      e.preventDefault();
      errorContainer.textContent = 'Pasted text would exceed character limit';
    }
  });

  // Initialize character count
  updateCharCount(promptInput);

 

  // Set up resize observer for dynamic content
  const resizeObserver = new ResizeObserver(() => {
    requestAnimationFrame(adjustPopupSize);
  });

  // Observe body for size changes
  resizeObserver.observe(document.body);

  // Event Listeners
//   if (advancedOptionsButton && categoriesContainer) {
//     // Remove any existing listeners first
//     advancedOptionsButton.replaceWith(advancedOptionsButton.cloneNode(true));
    
//     // Get the fresh reference
//     const newAdvancedOptionsButton = document.getElementById('advancedOptionsButton');
    
//     // Add the click listener
//     newAdvancedOptionsButton.addEventListener('click', function() {
//         // Toggle the hidden2 class
//         categoriesContainer.classList.toggle('hidden2');
        
//         // Log the current state
//         const isHidden = categoriesContainer.classList.contains('hidden2');
//         console.log('Advanced options panel toggled:', !isHidden);
        
//         // Make sure your hidden2 class is properly defined in CSS
//         if (!isHidden) {
//             categoriesContainer.style.display = 'grid'; // or 'block' depending on your layout
//         } else {
//             categoriesContainer.style.display = 'none';
//         }
        
//         // Adjust popup size after toggle
//         setTimeout(adjustPopupSize, 100);
//     });
// } else {
//     console.error('Advanced options elements not found:', {
//         button: !!advancedOptionsButton,
//         container: !!categoriesContainer
//     });
//   }
//   const style = document.createElement('style');
//   style.textContent = `
//      .hidden2 {
//     display: none !important;
// }

// #categories-container {
//     display: grid;
//     grid-template-columns: repeat(2, 1fr);
//     gap: 15px;
//     padding: 15px;
//     transition: all 0.3s ease;
//     opacity: 1;
//     transform: translateY(0);
// }

// #categories-container.hidden2 {
//     display: none !important;
//     opacity: 0;
//     transform: translateY(-10px);
// }

// #advancedOptionsButton {
//     cursor: pointer;
//     transition: all 0.3s ease;
// }

// #advancedOptionsButton:hover {
//     opacity: 0.8;
// }

// .category-card {
//     opacity: 1;
//     transform: translateY(0);
//     transition: all 0.3s ease;
// }

// .hidden2 .category-card {
//     opacity: 0;
//     transform: translateY(-10px);
// }

//   `;
//   document.head.appendChild(style);


//   fetch('http://https://thinkvelocity.in/api/python-api/get_categories')
//     .then(response => response.json())
//     .then(categories => {
//       console.log('Categories:', categories);
//       categories.forEach(category => {
//         const categoryCard = createCategoryCard(category);
//         categoriesContainer.appendChild(categoryCard);
//       });
//     })
//     .catch(error => {
//       console.error('Error fetching categories:', error);
//       categoriesContainer.textContent = `Failed to load categories. Error: ${error.message}`;
//     });

//   imageUpload.addEventListener('change', function (event) {
//     const fileName = event.target.files[0]?.name;
//     imageUploadText.textContent = fileName || 'Upload Image';
//   });

//  // sendButton.addEventListener('click', sendRequest);
//   //iconImage.addEventListener('click', sendRequest);  // Add this line to make the icon work as a generate button

//   document.addEventListener('click', closeAllDropdowns);

//   new MutationObserver(adjustPopupSize).observe(document.body, { childList: true, subtree: true });
//   adjustPopupSize();

//   // Radio group initialization
//   function initializeRadioGroup() {
//     if (radioGroup) {
//       radioGroup.addEventListener('click', function (event) {
//         if (event.target.classList.contains('radio-button')) {
//           radioGroup.querySelectorAll('.radio-button').forEach(btn =>
//             btn.classList.remove('selected')
//           );
//           event.target.classList.add('selected');
//         }
//       });
//     }
//   }

//   initializeRadioGroup();

//   function createCategoryCard(category) {
//     const categoryCard = document.createElement('div');
//     categoryCard.className = 'category-card';
    
//     const categoryTitle = document.createElement('div');
//     categoryTitle.className = 'category-title';
//     categoryTitle.textContent = category.name;
//     categoryCard.appendChild(categoryTitle);

//     // Create container for dropdowns
//     const dropdownsContainer = document.createElement('div');
//     dropdownsContainer.className = 'dropdowns-container flex gap-4';

//     // Create both dropdowns
//     category.dropdowns.forEach(dropdown => {
//         const dropdownContainer = createDropdown(dropdown);
//         dropdownsContainer.appendChild(dropdownContainer);
//     });

//     categoryCard.appendChild(dropdownsContainer);
//     return categoryCard;
// }



//   function updateDropdownButton(dropdownButton, selectedItem) {
//     const nameContainer = dropdownButton.querySelector('span');
//     nameContainer.textContent = selectedItem.querySelector('.dropdown-card-select').textContent;
//   }

//   function createDropdown(dropdown) {
//     const dropdownContainer = document.createElement('div');
//     dropdownContainer.className = 'dropdown flex-1';
//     dropdownContainer.setAttribute('data-default-text', dropdown.name);

//     const dropdownButton = document.createElement('button');
//     dropdownButton.className = 'dropdown-button';
//     dropdownButton.innerHTML = `
//         <div class="dropdown-button-content">
//             <span>${dropdown.name}</span>
//         </div>
//     `;

//     const dropdownContent = document.createElement('div');
//     dropdownContent.className = 'dropdown-content';
//     dropdownContent.style.display = 'none';

//     const horizontalContainer = document.createElement('div');
//     horizontalContainer.className = 'dropdown-horizontal-container';

//     dropdown.items.forEach(item => {
//         const card = document.createElement('div');
//         card.className = 'dropdown-card';
        
//         const button = document.createElement('button');
//         button.className = 'dropdown-card-select';
//         button.textContent = item.name;
        
//         card.appendChild(button);
//         horizontalContainer.appendChild(card);
//     });

//     dropdownContent.appendChild(horizontalContainer);
//     dropdownContainer.appendChild(dropdownButton);
//     dropdownContainer.appendChild(dropdownContent);

//     dropdownButton.addEventListener('click', function(e) {
//         e.stopPropagation();
//         const isVisible = dropdownContent.style.display === 'block';
//         closeAllDropdowns();
//         dropdownContent.style.display = isVisible ? 'none' : 'block';
//     });

//     return dropdownContainer;
// }






function getSelectedValues() {
  const selected = {};
  document.querySelectorAll('.category-card').forEach(card => {
      const categoryName = card.querySelector('.category-title').textContent;
      const selectedItems = Array.from(card.querySelectorAll('.dropdown-card.selected'))
          .map(card => card.textContent.trim());
      if (selectedItems.length > 0) {
          selected[categoryName] = selectedItems;
      }
  });
  return selected;
}
// document.addEventListener('click', function(e) {
//   if (!e.target.closest('.dropdown')) {
//       closeAllDropdowns();
//   }
// });

  function adjustDropdownWidth(dropdownContent) {
    if (!dropdownContent) return;
    const buttons = dropdownContent.querySelectorAll('button');
    const maxWidth = Math.max(...Array.from(buttons).map(button => button.offsetWidth));
    dropdownContent.style.width = `${maxWidth + 103}px`;
  }

  function adjustDropdownHeight(dropdownContent) {
    if (!dropdownContent) return;
    const cards = dropdownContent.querySelectorAll('.dropdown-card');
    if (cards.length > 0) {
      const cardHeight = cards[0].offsetHeight;
      dropdownContent.style.height = `${cardHeight + 20}px`;
    }
  }

  

  
  
  //   // Updated fetch for categories
  // function fetchCategories() {
  //   return fetch(`${API_BASE_URL}/get_categories`, {
  //     method: 'GET',
  //     headers: {
  //       'Accept': 'application/json',
  //     },
  //   })
  //   .then(response => {
  //     if (!response.ok) {
  //       throw new Error(`HTTP error! status: ${response.status}`);
  //     }
  //     return response.json();
  //   })
  //   .catch(error => {
  //     console.error('Error fetching categories:', error);
  //     // Show user-friendly error message
  //     const errorMessage = error.message === 'Failed to fetch' 
  //       ? 'Unable to connect to server. Please make sure the backend is running.'
  //       : `Error: ${error.message}`;
  //     throw new Error(errorMessage);
  //   });
  // }

  // Add this function at the appropriate scope level (same level as sendRequest)
  

  // Helper function to show errors
  

  // Updated sendRequest function
  


  // Helper functions

  
});


document.addEventListener('DOMContentLoaded', function() {
  // Delay the initialization slightly to ensure it doesn't interfere with other scripts
  setTimeout(addUnselectCapability, 100);
});

// dropdown
document.addEventListener('DOMContentLoaded', function () {
  initializeEnhanceToggle();
  initializeRadioGroup();
  initializeStyleButtons();
  //loadSavedSelections();
  const signupButton = document.getElementById('signupButton');
  const dropdownMenu = document.getElementById('dropdownMenu');
  const editButton = document.getElementById('editButton');
  //const logoutButton = document.getElementById('logoutButton');
  const editDropdownMenu = document.getElementById('editDropdownMenu');
  const accountButton = document.getElementById('accountButton');
  const editDeleteButtons = document.getElementById('editDeleteButtons');
  function navigateToLogin() {
    window.location.replace('login.html');
}



// if (logoutButton) {
//   logoutButton.addEventListener('click', function(e) {
//       e.preventDefault();
//       try {
//           localStorage.clear();
//           sessionStorage.clear();
          
//           // Clear cookies
//           document.cookie.split(";").forEach(function(c) {
//               document.cookie = c.replace(/^ +/, "")
//                   .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
//           });
          
//           window.location.replace('login.html');
//       } catch (error) {
//           console.error('Logout failed:', error);
//           showError('Logout failed. Please try again.');
//       }
//   });
// }


  // Initially hide the dropdowns
  // dropdownMenu.style.display = 'none';
  // editDropdownMenu.style.display = 'none';
  // editDeleteButtons.style.display = 'none';

  // // Toggle Sign Up dropdown
  // // signupButton.addEventListener('click', function (e) {
  // //   if(userId && token){
  // //   e.stopPropagation();
  // //   dropdownMenu.style.display = dropdownMenu.style.display === 'none' ? 'block' : 'none';
  // //   editDropdownMenu.style.display = 'none'; // Hide Edit dropdown when Sign Up is clicked
  // //   }
  // // });

  // // Toggle Edit dropdown
  // editButton.addEventListener('click', function (e) {
  //   e.stopPropagation();
  //   editDropdownMenu.style.display = editDropdownMenu.style.display === 'none' ? 'block' : 'none';
  //   dropdownMenu.style.display = 'none'; // Hide Sign Up dropdown when Edit is clicked
  // });

  // // Show Edit/Delete buttons when Account button is clicked
  // accountButton.addEventListener('click', function (e) {
  //   e.stopPropagation();
  //   signupButton.style.display = 'none'; // Hide Sign Up button
  //   editDeleteButtons.style.display = 'block'; // Show Edit/Delete buttons
  //   editDropdownMenu.style.display = 'none'; // Close the Edit dropdown if open
  // });

  // Close dropdowns when clicking outside
  // document.addEventListener('click', function (e) {
  //   if (e.target !== signupButton && e.target !== editButton && e.target !== accountButton) {
  //     //dropdownMenu.style.display = 'none';
  //     //editDropdownMenu.style.display = 'none'; // Hide Edit dropdown
  //     signupButton.style.display = 'flex'; // Show Sign Up button again
  //     editDeleteButtons.style.display = 'none'; // Hide Edit/Delete buttons
  //   }
  // });

  // Close dropdowns when pressing Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      dropdownMenu.style.display = 'none';
      editDropdownMenu.style.display = 'none'; // Hide Edit dropdown
      signupButton.style.display = 'flex'; // Show Sign Up button again
      editDeleteButtons.style.display = 'none'; // Hide Edit/Delete buttons
    }
  });
  // Initial UI update
  updateHeaderUI();
});

// Assuming the user ID is available, otherwise you can retrieve it from localStorage, cookies, etc.
let lastSavedPromptId = null;
let lastTokensUsed = 0; // To track tokens used in the last operation
// const userId = 'user123'; // Replace with the actual user ID (from session, localStorage, etc.)

// Fetch User Profile data
// console.log("checking user id:"+userId);
// fetch(`https://thinkvelocity.in/api/api/users/profile/${userId}`, {
//   method: 'GET',
//   headers: {
//     'Authorization': `Bearer ${token}` // Add the Authorization header with the token
//   }
// })
//   .then(response => response.json())
//   .then(data => {
//     // Assuming the API response has a 'name' field for the user's name
//     const userName = data.data.user.name;
//     console.log("data:" + data.data.user.name);
//     // Update the "Hii Nikhil" button with the user's name
//     document.getElementById('signupButton').textContent = `Hii ${userName}`; 
//     // signupButton
//     // document.getElementById('signupButton').textContent = ` ${userName}`;
//   })
//   .catch(error => console.error('Error fetching user profile:', error));

// Function to fetch and update credit display
async function updateCreditDisplay() {
  // console.log("checkng user id:"+userId + `https://thinkvelocity.in/api/api/token-types/${userId}`);
  // console.log("checkng token:"+token);

  try {
    const response = await fetch(`https://thinkvelocity.in/api/api/token-types/${userId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      }
    });
    const data = await response.json();
    console.log("data:"+data.data.token_received);
    const tokensReceived = data.data.token_received;
    const tokensUsed = data.data.tokens_used;
    const remainingCredits = tokensReceived - tokensUsed;

    // Update the button content with icon and credit count
    const editButton = document.getElementById('editButton');
    editButton.innerHTML = `
      <span><img class="coinicon" src="./assets/coin1.png" alt="coin"></span>
      <span>${remainingCredits}</span>
    `;
  } catch (error) {
    console.error('Error updating credit display:', error);
  }
}
  



// This is the function that will be triggered when the "Generate" button is clicked
function handleCreditDeduction(feature) {
  return new Promise((resolve, reject) => {
      fetch('https://thinkvelocity.in/api/api/credit/credits', {
          method: 'GET',
          headers: {
              'Authorization': `Bearer ${token}`
          }
      })
      .then(response => response.json())
      .then(data => {
          const featureCredit = data.data.find(credit => credit.feature === feature);
          if (!featureCredit) {
              reject('Feature not found');
              return;
          }

          fetch(`https://thinkvelocity.in/api/api/token-types/${userId}`, {
              method: 'GET',
              headers: {
                  'Authorization': `Bearer ${token}`,
              }
          })
          .then(response => response.json())
          .then(data => {
              const tokensReceived = data.data.token_received;
              const tokensUsed = data.data.tokens_used;

              if (tokensReceived <= tokensUsed) {
                  reject('Out of tokens');
                  return;
              }

              if (tokensReceived - tokensUsed >= featureCredit.credits) {
                  const updatedTokensUsed = tokensUsed + featureCredit.credits;
                  lastTokensUsed = featureCredit.credits; // Track tokens used

                  fetch(`https://thinkvelocity.in/api/api/token-types/${userId}`, {
                      method: 'PUT',
                      headers: {
                          'Content-Type': 'application/json',
                          'Authorization': `Bearer ${token}`,
                      },
                      body: JSON.stringify({
                          tokens_used: updatedTokensUsed,
                          token_received: tokensReceived
                      })
                  })
                  .then(updateResponse => updateResponse.json())
                  .then(async (updateData) => {
                      await updateCreditDisplay();
                      resolve(featureCredit.credits);
                  })
                  .catch(error => reject(error));
              } else {
                  reject('Not enough tokens');
              }
          });
      })
      .catch(error => reject(error));
  });
}

// Feature usage tracking
let promptUsed = false;


//document.addEventListener('DOMContentLoaded', initializeRadioGroups);

// Event listener for basic prompt
document.getElementById('promptInput').addEventListener('change', function () {
  promptUsed = true; // Mark basic prompt as used
});

// Event listeners for advanced option buttons
const advancedOptionButtons = document.querySelectorAll('.dropdown-card');
advancedOptionButtons.forEach(button => {
    button.addEventListener('click', function() {
    const optionId = this.querySelector('.dropdown-card-select').innerText; // Use button text as unique identifier
    console.log(`Advanced option clicked: ${optionId}`); // Log button click
    // advancedOptionsUsed = true;

    // Toggle the selected option
    if (!advancedOptionsSelected.has(optionId)) {
      // Add option to the selected set
      advancedOptionsSelected.add(optionId);
      // Mark the option as selected visually
      this.classList.add('selected');
    } else {
      // Remove option from the selected set
      advancedOptionsSelected.delete(optionId);
      // Remove the selected state visually
      this.classList.remove('selected');
    }

    // Update the flag for advanced options usage based on the size of the set
    advancedOptionsUsed = advancedOptionsSelected.size > 0;

    // Log the state of advancedOptionsUsed and the selected set
    console.log('Advanced options selected:', Array.from(advancedOptionsSelected));
    console.log('Advanced options used:', advancedOptionsUsed);

    // Debugging: Verify if the flag is correctly updated
    if (advancedOptionsUsed) {
      console.log('At least one advanced option is selected');
    } else {
      console.log('No advanced options are selected');
    }
  });
});

// Event listener for generate button
document.getElementById('sendButton').addEventListener('click', async function () {
  if (!userId || !token) {
    showLoginError();
    //showError("Please login to continue");
    return;
  }
    //document.getElementById('promptInput').disabled = true;
    
    const promptInput = document.getElementById('promptInput');
    const errorContainer = document.querySelector('.error-message-container');

    if (!promptInput || !promptInput.value.trim()) {
      showTextBoxError('Please enter a prompt first');
      // promptInput.style.border = '0.2px solid red';

      // // Add error message
      // if (errorContainer) {
      //   errorContainer.textContent = 'Please enter a prompt first';
      //   errorContainer.style.color = 'red';
      // } else {
      //   // Create error container if it doesn't exist
      //   const newErrorContainer = document.createElement('div');
      //   newErrorContainer.className = 'error-message-container text-red-500 text-sm mt-1';
      //   newErrorContainer.textContent = 'Please enter a prompt text';
      //   promptInput.parentNode.appendChild(newErrorContainer);
      // }
      
      return;
    }
    else{
      document.getElementById('promptInput').disabled = true;
    }
  
    try {
      //promptInput.disabled = true;
      
      // Remove any existing error styling
      promptInput.classList.remove('border-2', 'border-red-500');
      if (errorContainer) {
        errorContainer.textContent = '';
      }
  
      const hasImage = document.getElementById('imageUpload') && document.getElementById('imageUpload').files.length > 0;
  
      // Proceed with request
      await sendRequest();
  
    } catch (error) {
      console.error('Error during processing:', error);
      showError(`Error: ${error.message}`);
    } finally {
      resetInterface();
    }
  });
  

async function verifyAndRecordFeatures() {
  try {
    
    const selectedStyle = getSelectedStyle();
    const selectedPlatform = getSelectedPlatform();
  //   const { selectedStyle, selectedPlatform } = await chrome.storage.local.get([
  //     'selectedStyle',
  //     'selectedPlatform'
  // ]);
  
    // if (!currentStyle) {
    //   throw new Error('Please select a style');
    // }

    // if (!currentPlatform) {
    //   throw new Error('Please select a platform');
    // }

    // Get current token balance
    const tokenResponse = await fetch(`https://thinkvelocity.in/api/api/token-types/${userId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      }
    });
    const tokenData = await tokenResponse.json();
    const availableTokens = tokenData.data.token_received - tokenData.data.tokens_used;

    // Get feature costs
    const creditsResponse = await fetch('https://thinkvelocity.in/api/api/credit/credits', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    const creditsData = await creditsResponse.json();
    
    // Calculate total required tokens
    let requiredTokens = 0;

    // Add base prompt cost
    const basicFeature = creditsData.data.find(credit => credit.feature === 'basic_prompt');
    console.log("basic feature cost:"+basicFeature?.credits);
    requiredTokens += basicFeature?.credits || 0;
    console.log("required tokens:"+requiredTokens + "Selected style:"+selectedStyle + "selected platform:"+selectedPlatform);

    if(selectedStyle){
    // Add style cost
    const styleFeature = creditsData.data.find(credit => 
      credit.feature === `style_prompt`
    );
    if (styleFeature) {
      requiredTokens += styleFeature.credits;
    }
  }
  if(selectedPlatform){

    // Add platform cost
    const platformFeature = creditsData.data.find(credit => 
      credit.feature === `platform`
    );
    if (platformFeature) {
      requiredTokens += platformFeature.credits;
    }
  }

    // Check if enough tokens are available
    if (availableTokens < requiredTokens) {
      trackEvent("Out of Tokens",
        {
          availableTokens:availableTokens,
          requiredTokens:requiredTokens
        }
      )
      showTokenError(); 
      showError('Not enough credits available. Please top up your credits.');
      return false;
    }

    // Verify feature access
    const accessChecks = await Promise.all([
      checkFeatureAccess('1'), // Basic
      checkFeatureAccess('2'), // Style
      checkFeatureAccess('3')  // Platform
    ]);

    const [basicAccess, styleAccess, platformAccess] = accessChecks;

    // Check each access result
    if (!basicAccess.data.canUse) {
      showError(basicAccess.data.reason === 'timeout'
        ? `Basic features locked until ${new Date(basicAccess.data.timeoutUntil).toLocaleTimeString()}`
        : `Daily limit reached for basic features`);
      return false;
    }

    if (!styleAccess.data.canUse) {
      showError(styleAccess.data.reason === 'timeout'
        ? `Style features locked until ${new Date(styleAccess.data.timeoutUntil).toLocaleTimeString()}`
        : `Daily limit reached for style features`);
      return false;
    }

    if (!platformAccess.data.canUse) {
      showError(platformAccess.data.reason === 'timeout'
        ? `Platform features locked until ${new Date(platformAccess.data.timeoutUntil).toLocaleTimeString()}`
        : `Daily limit reached for platform features`);
      return false;
    }

    return true;
  } catch (error) {
    console.error('Error checking feature access:', error);
    showError(error.message || "Error verifying feature access. Please try again.");
    return false;
  }
}


async function handleCreditDeductions() {
//   const { selectedStyle, selectedPlatform } = await chrome.storage.local.get([
//     'selectedStyle',
//     'selectedPlatform'
// ]);
const selectedStyle = getSelectedStyle();
const selectedPlatform = getSelectedPlatform();
  try {
    // Record basic prompt usage and deduct credits
    await recordFeatureUsage('1');
    await handleCreditDeduction('basic_prompt');
    console.log("is style selected:"+selectedStyle);
    // Record style usage and deduct credits
    if (selectedStyle) {
      await recordFeatureUsage('2');
      await handleCreditDeduction(`style_prompt`);
    }
    console.log("is platform selected:"+selectedPlatform);
    // Record platform usage and deduct credits
    if (selectedPlatform) {
      await recordFeatureUsage('3');
      await handleCreditDeduction(`platform`);
    }
    
    // Update the display
    await updateCreditDisplay();
    return true;
  } catch (error) {
    console.error('Error handling credit deductions:', error);
    showError('Error processing credits. Please contact support.');
    return false;
  }
}



function resetInterface() {
  // Enable input
  document.getElementById('promptInput').disabled = false;
  
  // Clear prompt input
  const promptInput = document.getElementById('promptInput');
  if (promptInput) {
    promptInput.value = '';
    chrome.storage.local.remove(['promptText']);
  }
  
  // Update credits display
  updateCalculatedCredits();
  updateCreditDisplay();
}



// Initial credit display update when page loads
updateCreditDisplay();

    // Define logout function
    function logout() {
      try {
        // Clear all stored data
        localStorage.clear();
        sessionStorage.clear();

        // Clear cookies
        document.cookie.split(";").forEach(function (c) {
          document.cookie = c.replace(/^ +/, "")
            .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
        });

        // Redirect to login page
        window.location.href = 'login.html';
      } catch (error) {
        console.error('Logout failed:', error);
        alert('Logout failed. Please try again.');
      }
    }
    window.logout = logout;

    // Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function () {
  const copyButton = document.getElementById('copyButton');
  const textarea = document.getElementById('promptInput');
  
  copyButton.addEventListener('click', function () {
      const textToCopy = textarea.value;
      if (!textToCopy) {
          showError('Please enter text to copy');
          return;
      }
      trackEvent("Copied Prompt",
        {
          type:"Original"
        }
      );
      // Copy the text to clipboard
      navigator.clipboard.writeText(textToCopy)
          .then(() => {
              // Add the white animation class
              copyButton.classList.add('white');
              
              // Remove the class after 2 seconds
              setTimeout(() => {
                  copyButton.classList.remove('white');
              }, 2000);
          })
          .catch(() => {
              // Fallback for older browsers
              fallbackCopyTextToClipboard(textarea);
          });
  });
  
  // Fallback function for older browsers
  function fallbackCopyTextToClipboard(textarea) {
      try {
          textarea.select();
          textarea.setSelectionRange(0, 99999);
          document.execCommand('copy');
          window.getSelection().removeAllRanges();
          
          // Add the white animation class
          copyButton.classList.add('white');
          
          // Remove the class after 2 seconds
          setTimeout(() => {
              copyButton.classList.remove('white');
          }, 2000);
      } catch (err) {
          alert('Failed to copy text. Please try again.');
          console.error('Failed to copy text:', err);
      }
  }
});

