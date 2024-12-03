let ports = [];
let injectedTabs = new Set();

chrome.runtime.onConnect.addListener((port) => {
    ports.push(port);
    console.log('New connection established');
  
    port.onDisconnect.addListener(() => {
      ports = ports.filter(p => p !== port);
    });
  });
  
  
  chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && 
        tab.url?.startsWith('http://localhost:5173')) {
      chrome.scripting.executeScript({
        target: { tabId },
        files: ['content-script.js']
      }).catch(error => console.error('Script injection error:', error));
    }
  });
  
  
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Received message:', message);
  
    if (message.type === 'AUTH_CHANGED') {
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
    else if (message.action === 'updateTabs') {
      chrome.storage.local.set({ 'enhanceButtonEnabled': message.enabled });
      updateAllTabs(message.enabled);
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
        }
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