let ports = [];

chrome.runtime.onConnect.addListener((port) => {
    ports.push(port);
    console.log('New connection established');
  
    port.onDisconnect.addListener(() => {
      ports = ports.filter(p => p !== port);
    });
  });
  
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'LOGIN_STATUS') {
      chrome.storage.local.set({ 'token': request.token, 'userData': request.userData });
      // Broadcast to all extension pages
      chrome.runtime.sendMessage({ type: 'AUTH_CHANGED', isLoggedIn: true });
    } else if (request.type === 'LOGOUT') {
      chrome.storage.local.remove(['token', 'userData']);
      chrome.runtime.sendMessage({ type: 'AUTH_CHANGED', isLoggedIn: false });
    }
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
    // Always return true for asynchronous response
    return true;
  });
      chrome.runtime.onInstalled.addListener(function() {
      // Initialize storage
      chrome.storage.local.get(['userToken'], function(result) {
          if (!result.userToken) {
              chrome.action.setPopup({ popup: 'login.html' });
          } else {
              chrome.action.setPopup({ popup: 'phase1.html' });
          }
      });
  });
  
  chrome.storage.onChanged.addListener(function(changes, namespace) {
      if (changes.userToken && changes.userToken.newValue) {
          chrome.action.setPopup({ popup: 'phase1.html' });
      }
  });