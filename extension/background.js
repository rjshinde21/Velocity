let ports = [];
let injectedTabs = new Set();
let authState = null; // Store auth state in memory
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
            port.postMessage({
              type: 'AUTH_STATE_CHANGED',
              data: message.data
            });
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
    return url && !url.startsWith('chrome://') && 
           !url.startsWith('brave://') && 
           !url.startsWith('chrome-extension://');
  }
  
  async function injectContentScript(tabId) {
    try {
      await chrome.scripting.executeScript({
        target: { tabId },
        files: ['content-script.js']
      });
      
      injectedTabs.add(tabId);
      
      const state = await chrome.storage.local.get(['enhanceButtonEnabled']);
      await chrome.tabs.sendMessage(tabId, {
        action: 'toggleEnhanceButton',
        enabled: state.enhanceButtonEnabled === true
      });
      if (authState) {
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
  