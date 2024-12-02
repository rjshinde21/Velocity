// // background.js
// let injectedTabs = new Set();

// // Listen for tab updates
// chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
//   if (changeInfo.status === 'complete') {
//     // Only inject if not already injected
//     if (!injectedTabs.has(tabId) && isValidUrl(tab.url)) {
//       injectContentScript(tabId);
//     }
//   }
// });

// // Clean up when tabs are closed
// chrome.tabs.onRemoved.addListener((tabId) => {
//   injectedTabs.delete(tabId);
// });

// // Helper to check if URL is valid for injection
// function isValidUrl(url) {
//   if (!url) return false;
//   return !url.startsWith('chrome://') && 
//          !url.startsWith('brave://') && 
//          !url.startsWith('chrome-extension://');
         
// }

// // Handle script injection
// async function injectContentScript(tabId) {
//   try {
//     await chrome.scripting.executeScript({
//       target: { tabId },
//       files: ['content.js']
//     });
//     injectedTabs.add(tabId);
    
//     // After injection, send the current state
//     chrome.storage.local.get(['enhanceButtonEnabled'], (result) => {
//       chrome.tabs.sendMessage(tabId, {
//         action: 'toggleEnhanceButton',
//         enabled: result.enhanceButtonEnabled === true
//       }).catch(() => {
//         // Ignore errors here as the content script might not be ready yet
//       });
//     });
//   } catch (error) {
//     console.log(`Script injection failed for tab ${tabId}:`, error);
//   }
// }

// chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
//     if (message.action === 'updateTabs') {
//       chrome.storage.local.set({ 'enhanceButtonEnabled': message.enabled });
//       updateAllTabs(message.enabled);
//     }
//   });

// // Function to update all valid tabs
// async function updateAllTabs(enabled) {
//   const tabs = await chrome.tabs.query({});
//   for (const tab of tabs) {
//     if (isValidUrl(tab.url)) {
//       try {
//         if (!injectedTabs.has(tab.id)) {
//           await injectContentScript(tab.id);
//         }
//         await chrome.tabs.sendMessage(tab.id, {
//           action: 'toggleEnhanceButton',
//           enabled
//         });
//       } catch (error) {
//         console.log(`Could not update tab ${tab.id}:`, error);
//       }
//     }
//   }
// }
let injectedTabs = new Set();

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
      files: ['content.js']
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

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'updateTabs') {
    chrome.storage.local.set({ 'enhanceButtonEnabled': message.enabled });
    updateAllTabs(message.enabled);
  }
});

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