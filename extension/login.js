document.addEventListener('DOMContentLoaded', function() {
    const loginButton = document.getElementById('loginButton');
    const loginButton2 = document.getElementById('loginButton2');
    const signupButton = document.getElementById('signupButton');
    
    // Check if already logged in via web app
    checkWebAppAuthStatus();

    // Regular login handler
    if (loginButton) {
        loginButton.addEventListener('click', async function(e) {
            e.preventDefault();
            await loginUser();
        });
    }

    // Google login handler
    if (loginButton2) {
        loginButton2.addEventListener('click', function(e) {
            e.preventDefault();
            // Redirect to web app's login page for Google auth
            window.open('http://localhost:3001/login', '_blank');
        });
    }

    // Listen for auth changes from web app
    window.addEventListener('storage', function(e) {
        if (e.key === 'token' || e.key === 'userId' || e.key === 'userData') {
            checkWebAppAuthStatus();
        }
    });
});
async function checkWebAppAuthStatus() {
    // Check web app's local storage for auth data
    const token = localStorage.getItem('userToken');
    const userId = localStorage.getItem('userId');
    const userData = localStorage.getItem('userData');

    if (token && userId) {
        try {
            // Verify token with backend
            const response = await fetch(`http://localhost:3001/api/users/profile/${userId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const verifiedData = await response.json();
                // Store in extension's storage
                chrome.storage.local.set({
                    'userToken': token,
                    'userId': userId,
                    'userData': userData
                }, function() {
                    // Redirect to extension's main page
                    window.location.href = 'phase1.html';
                });
            } else {
                // Clear invalid auth data
                clearAuthData();
            }
        } catch (error) {
            console.error('Auth verification error:', error);
            clearAuthData();
        }
    }
}

async function loginUser() {
    const email = document.getElementById('email')?.value?.trim() || '';
    const password = document.getElementById('password')?.value || '';
    const responseDiv = document.getElementById('response');
    const loadingDiv = document.getElementById('loading');

    if (loadingDiv) loadingDiv.style.display = 'block';
    if (responseDiv) responseDiv.style.display = 'none';

    if (!email || !password) {
        showError('Please enter both email and password');
        return;
    }

    try {
        const response = await fetch('http://localhost:3001/api/users/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok && data.data?.token) {
            // Store auth data in both local storage and extension storage
            const authData = {
                userToken: data.data.token,
                userId: data.data.user.id,
                userData: JSON.stringify(data.data.user)
            };

            // Store in local storage
            localStorage.setItem('userToken', authData.userToken);
            localStorage.setItem('userId', authData.userId);
            localStorage.setItem('userData', authData.userData);

            // Store in extension storage
            chrome.storage.local.set(authData, function() {
                window.location.href = 'phase1.html';
            });
        } else {
            showError(data.message || 'Login failed. Please try again.');
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('Network error. Please try again.');
    } finally {
        if (loadingDiv) loadingDiv.style.display = 'none';
    }
}
function clearAuthData() {
    // Clear local storage
    localStorage.removeItem('userToken');
    localStorage.removeItem('userId');
    localStorage.removeItem('userData');

    // Clear extension storage
    chrome.storage.local.remove(['userToken', 'userId', 'userData']);
}

function setLoading(isLoading) {
    const loginButton2 = document.getElementById('loginButton2');
    if (!loginButton2) return;

    if (isLoading) {
        loginButton2.disabled = true;
        loginButton2.innerHTML = `
            <span class="loading-spinner"></span>
            Connecting...
        `;
    } else {
        loginButton2.disabled = false;
        loginButton2.innerHTML = 'Sign in with Google';
    }
}

  function updateUserInterface(user) {
    const signupButton = document.getElementById('signupButton');
    const editButton = document.getElementById('editButton');
    
    if (user) {
      signupButton.innerHTML = `
        <span><img class="profileicon" src="./assets/profile.png" alt=""></span>
        Hi ${user.name}!
      `;
      if (editButton) {
        editButton.style.display = 'flex';
      }
    } else {
      signupButton.innerHTML = `
        <span><img class="profileicon" src="./assets/profile.png" alt=""></span>
        Sign in with Google
      `;
      if (editButton) {
        editButton.style.display = 'none';
      }
    }
  }
    
async function checkAuthAndRedirect(token, userId) {
    try {
        const response = await fetch(`http://localhost:3001/api/users/profile/${userId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            window.location.href = 'phase1.html';
        } else {
            // Token invalid, clear storage
            localStorage.removeItem('userToken');
            localStorage.removeItem('userEmail');
            localStorage.removeItem('userId');
        }
    } catch (error) {
        console.error('Auth check error:', error);
    }
}


function showError(message) {
    const responseDiv = document.getElementById('response');
    const loadingDiv = document.getElementById('loading');

    if (loadingDiv) loadingDiv.style.display = 'none';
    
    if (responseDiv) {
        responseDiv.style.display = 'block';
        responseDiv.style.backgroundColor = '#f2dede';
        responseDiv.innerHTML = `<div class="error">${message}</div>`;
        console.error('Error shown:', message);
    }
}

// Utility function to check if token is expired
function isTokenExpired(token) {
    if (!token) return true;
    try {
        const [, payload] = token.split('.');
        const decodedPayload = JSON.parse(atob(payload));
        const currentTime = Math.floor(Date.now() / 1000);
        return decodedPayload.exp < currentTime;
    } catch {
        return true;
    }
}


// Utility function to make authenticated requests
async function makeAuthenticatedRequest(url, options = {}) {
    const token = await new Promise(resolve => {
        chrome.storage.local.get('userToken', data => resolve(data.userToken));
    });
    
    if (!token) {
        throw new Error('No authentication token found');
    }

    return fetch(url, {
        ...options,
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...options.headers
        }
    });
}
