// contentScript.js
// This script runs in the context of the web page
let lastAuthState = null;

// Function to check auth state
function checkAuthState() {
        // Get token first
        const token = localStorage.getItem('token');
        console.log('Retrieved token:', token); // Debug log
    
  const authData = {    
    isAuthenticated: localStorage.getItem('token'),
    token: localStorage.getItem('token'),
    userId: localStorage.getItem('userId'),
    userName: localStorage.getItem('userName'),
    userEmail: localStorage.getItem('userEmail')
  };

  // Only send message if auth state has changed
  if (JSON.stringify(authData) !== JSON.stringify(lastAuthState)) {
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