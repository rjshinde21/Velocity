chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "adjustSize") {
        chrome.windows.getCurrent(window => {
            const width = Math.max(request.width, 400); // minimum width
            const height = Math.max(request.height, 300); // minimum height
            
            chrome.windows.update(window.id, {
                width: width + 50, // Add padding for window chrome
                height: height + 100 // Add padding for window chrome
            }).catch(error => {
                console.log('Window adjustment failed:', error);
            });
        });
    }
    return true; // Required for async response
  });
  
  chrome.runtime.onInstalled.addListener(function() {
      // Initialize storage
      chrome.storage.local.get(['userToken'], function(result) {
          if (!result.userToken) {
              chrome.action.setPopup({ popup: 'login.html' });
          } else {
              chrome.action.setPopup({ popup: 'popup.html' });
          }
      });
  });
  
  chrome.storage.onChanged.addListener(function(changes, namespace) {
      if (changes.userToken && changes.userToken.newValue) {
          chrome.action.setPopup({ popup: 'popup.html' });
      }
  });