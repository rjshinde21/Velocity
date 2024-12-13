let ports = [];
let injectedTabs = new Set();
let authState = null; // Store auth state in memory
let eventQueue = [];
const MIXPANEL_TOKEN = "48a67766d0bb1b3399a4f956da9c52da";
const MIXPANEL_API_URL = "https://api-js.mixpanel.com/track/?verbose=1&ip=1&data=";
function encodeData(data) {
  return btoa(JSON.stringify(data));
}


function sendToMixpanel(event) {
  const data = {
      event: event.name,
      properties: {
          ...event.properties,
          token: MIXPANEL_TOKEN,
          time: Date.now(),
          distinct_id: 'anonymous', // Or use actual user ID if available
          $insert_id: Date.now().toString(), // Ensure event uniqueness
          $os: navigator.platform,
          $browser: 'Chrome',
          $browser_version: /Chrome\/([0-9.]+)/.exec(navigator.userAgent)[1],
          mp_lib: 'chrome-extension'
      }
  };

  const encodedData = encodeData(data);
  const url = MIXPANEL_API_URL + encodedData;

  fetch(url, {
      method: 'GET',
      mode: 'no-cors'
  })
  .then(() => {
      // Also send to debug endpoint to verify
      fetch(`https://api-js.mixpanel.com/track/?verbose=1&data=${encodedData}`)
          .then(response => response.json())
          .then(data => {
              console.log('Mixpanel debug response:', data);
          })
          .catch(error => {
              console.error('Debug endpoint error:', error);
          });
          
      console.log('Event sent to Mixpanel:', event.name, 'with properties:', event.properties);
  })
  .catch(error => {
      console.error('Mixpanel tracking error:', error);
  });
}


const SUPPORTED_PLATFORMS = {
  chatgpt: {
    urlPattern: /^https:\/\/chatgpt\.com/,
    selectors: '#prompt-textarea',
    name: 'GPT'
  },
  claude: {
    urlPattern: /^https:\/\/claude\.ai/,
    selectors: '.claude-textarea, div[contenteditable="true"]',
    name: 'Claude'
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
    selectors: 'textarea, [contenteditable="true"], input[type="text"], .cm-content',
    name: 'Runway'
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
function isDiscordUrl(url) {
  return SUPPORTED_PLATFORMS.discord.urlPattern.test(url);
}

chrome.storage.local.get([
  'isAuthenticated',
  'token',
  'userId',
  'userName',
  'userEmail'
], (result) => {
  authState = {
    isAuthenticated: result.isAuthenticated,
    token: result.token,
    userId: result.userId,
    userName: result.userName,
    userEmail: result.userEmail
  };
});

chrome.runtime.onConnect.addListener((port) => {
  ports.push(port);
  console.log('New connection established');

  // Send current auth state to new connection if it exists
  if (authState) {
    try {
      port.postMessage({
        type: 'AUTH_STATE_CHANGED',
        data: authState
      });
    } catch (error) {
      console.error('Error sending initial auth state:', error);
    }
  }

  port.onDisconnect.addListener(() => {
    ports = ports.filter(p => p !== port);
  });
});

async function checkUserTokens(token, userId) {
  try {
    const response = await fetch(`https://thinkvelocity.in/api/api/token-types/${userId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    const data = await response.json();
    return {
      hasTokens: data.data.token_received > data.data.tokens_used,
      remainingTokens: data.data.token_received - data.data.tokens_used
    };
  } catch (error) {
    console.error('Error checking tokens:', error);
    return { hasTokens: false, remainingTokens: 0 };
  }
}

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && 
        tab.url?.startsWith('https://thinkvelocity.in/')) {
      chrome.scripting.executeScript({
        target: { tabId },
        files: ['content-script.js']
      }).catch(error => console.error('Script injection error:', error));
    }
  });
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Received message:', message);
  
    if (message.type === 'AUTH_CHANGED') {
      if (sender.tab && isDiscordUrl(sender.tab.url)) {
        console.log('Ignoring auth state change from Discord');
        return true;
      }
  
      // Update stored auth state
      authState = message.data;
      
      // Store auth data
      chrome.storage.local.set({
        isAuthenticated: message.data.isAuthenticated,
        token: message.data.token,
        userId: message.data.userId,
        userName: message.data.userName,
        userEmail: message.data.userEmail
      }, () => {
        console.log('Auth data stored in extension');
        // Notify all connected ports
        ports.forEach(port => {
          try {
            if (port.sender && !isDiscordUrl(port.sender.tab?.url)) {
            port.postMessage({
              type: 'AUTH_STATE_CHANGED',
              data: message.data
            });
          }
          } catch (error) {
            console.error('Error sending message to port:', error);
          }
        });
      });
    }
    if (message.action === 'updateTabs') {
      // First check authentication and tokens
      chrome.storage.local.get(['token', 'isAuthenticated', 'userId'], async (result) => {
        if (!result.isAuthenticated || !result.token) {
          // User is not authenticated
          sendResponse({
            success: false,
            error: 'Please log in to use this feature',
            type: 'auth'
          });
          return;
        }
  
        // Check tokens
        const tokenStatus = await checkUserTokens(result.token, result.userId);
        if (!tokenStatus.hasTokens) {
          sendResponse({
            success: false,
            error: 'Insufficient tokens. Please purchase more tokens to continue.',
            type: 'tokens',
            remainingTokens: tokenStatus.remainingTokens
          });
          return;
        }
  
        // If all checks pass, proceed with the update
        chrome.storage.local.set({ 'enhanceButtonEnabled': message.enabled });
        updateAllTabs(message.enabled);
        sendResponse({ success: true });
      });
      return true; // Will respond asynchronously
    }
    if (message.type === 'TRACK_EVENT') {
        sendToMixpanel({
          name: message.eventName,
          properties: {
              ...message.properties,
              url: sender.tab?.url,
              $browser: 'Chrome',
              $browser_version: /Chrome\/([0-9.]+)/.exec(navigator.userAgent)[1],
              mp_lib: 'chrome-extension'
          }
      });
      sendResponse({ status: 'success' });
  }
    // Always return true for asynchronous response
    return true;
  });


  // chrome.storage.onChanged.addListener(function(changes, namespace) {
  //     if (changes.token && changes.token.newValue) {
  //         chrome.action.setPopup({ popup: 'phase1.html' });
  //     }
  // });

  chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && !injectedTabs.has(tabId) && isValidUrl(tab.url)) {
      injectContentScript(tabId);
    }
  });
  
  
  chrome.tabs.onRemoved.addListener((tabId) => {
    injectedTabs.delete(tabId);
  });
  
  function isValidUrl(url) {
    // First check basic invalid URLs
    if (!url || 
        url.startsWith('chrome://') || 
        url.startsWith('brave://') || 
        url.startsWith('chrome-extension://')) {
      return false;
    }
  
    // Then check if URL matches any supported platform
    return Object.values(SUPPORTED_PLATFORMS).some(platform => 
      platform.urlPattern.test(url)
    );
    }
  
  
  async function injectContentScript(tabId) {
    try {
      // Get tab info to check URL
      const tab = await chrome.tabs.get(tabId);
      if (!isValidUrl(tab.url)) {
        console.log('Skipping injection for unsupported URL:', tab.url);
        return;
      }
  
      await chrome.scripting.executeScript({
        target: { tabId },
        files: ['content-script.js']
      });
      
      injectedTabs.add(tabId);
      
      // Only send messages if it's a supported platform
      const state = await chrome.storage.local.get(['enhanceButtonEnabled']);
      await chrome.tabs.sendMessage(tabId, {
        action: 'toggleEnhanceButton',
        enabled: state.enhanceButtonEnabled === true
      });
      
      if (authState && !isDiscordUrl(tab.url)) {
        await chrome.tabs.sendMessage(tabId, {
          type: 'AUTH_STATE_CHANGED',
          data: authState
        });
      }
    } catch (error) {
      console.log(`Script injection failed for tab ${tabId}:`, error);
    }
  }
  
  

  
  async function updateAllTabs(enabled) {
    const tabs = await chrome.tabs.query({});
    for (const tab of tabs) {
      if (isValidUrl(tab.url)) {
        if (!injectedTabs.has(tab.id)) {
          await injectContentScript(tab.id);
        } else {
          try {
            await chrome.tabs.sendMessage(tab.id, {
              action: 'toggleEnhanceButton',
              enabled
            });
          } catch (error) {
            console.log(`Could not update tab ${tab.id}:`, error);
          }
        }
      }
    }
  }
  