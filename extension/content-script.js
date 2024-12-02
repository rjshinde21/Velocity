// content-script.js
// Add this to your extension to monitor web app auth changes
let lastKnownToken = null;

// Check local storage periodically for auth changes
setInterval(() => {
    const currentToken = localStorage.getItem('userToken');
    
    if (currentToken !== lastKnownToken) {
        lastKnownToken = currentToken;
        
        if (currentToken) {
            // User logged in or token changed
            const userId = localStorage.getItem('userId');
            const userData = localStorage.getItem('userData');
            
            chrome.runtime.sendMessage({
                type: 'AUTH_CHANGED',
                data: {
                    token: currentToken,
                    userId: userId,
                    userData: userData
                }
            });
        } else {
            // User logged out
            chrome.runtime.sendMessage({
                type: 'AUTH_CHANGED',
                data: null
            });
        }
    }
}, 1000);  // Check every second