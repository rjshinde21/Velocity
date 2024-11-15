document.addEventListener('DOMContentLoaded', function() {
    const loginButton = document.getElementById('loginButton');
    const signupButton = document.getElementById('signupButton');
    
    // Check if already logged in
    const token = localStorage.getItem('userToken');
    const userId = localStorage.getItem('userId'); // Add userId storage
    if (token && userId) {
        checkAuthAndRedirect(token, userId);
    }

    if (loginButton) {
        loginButton.addEventListener('click', async function(e) {
            e.preventDefault();
            await loginUser();
        });
    }

    if (signupButton) {
        signupButton.addEventListener('click', function(e) {
            e.preventDefault();
            chrome.tabs.create({
                url: 'https://www.toteminteractive.in/velocity_lander/index.html'
            });
            window.close();
        });
    }
});

async function checkAuthAndRedirect(token, userId) {
    try {
        const response = await fetch(`http://localhost:3000/api/users/profile/${userId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            window.location.href = 'popup.html';
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

async function loginUser() {
    const email = document.getElementById('email')?.value?.trim() || '';
    const password = document.getElementById('password')?.value || '';
    const responseDiv = document.getElementById('response');
    const loadingDiv = document.getElementById('loading');

    // Reset UI
    if (responseDiv) responseDiv.style.display = 'none';
    if (loadingDiv) loadingDiv.style.display = 'block';

    // Validate inputs
    if (!email || !password) {
        showError('Please enter both email and password');
        return;
    }

    try {
        console.log('Attempting login with:', { email });

        const response = await fetch('http://localhost:3000/api/users/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        console.log('Response status:', response.status);

        if (loadingDiv) loadingDiv.style.display = 'none';

        const data = await response.json();
        console.log('Full Login Response:', data);

        // Log specific data structure
        console.log('User ID from response:', data.data?.user?.id);
        console.log('Token from response:', data.data?.token);

        if (response.ok && data.data?.token) {
            // Store token and user data
            const token = data.data.token;
            const userId = data.data.user.id; // Changed to match your API response structure
            
            console.log('Storing user data:', {
                token: token ? 'Present' : 'Missing',
                userId,
                email
            });
            
            localStorage.setItem('userToken', token);
            localStorage.setItem('userEmail', email);
            localStorage.setItem('userId', userId);

            // Log stored values
            console.log('Stored values:', {
                storedToken: localStorage.getItem('userToken'),
                storedUserId: localStorage.getItem('userId'),
                storedEmail: localStorage.getItem('userEmail')
            });
            console.log("api called::+ "+ `http://localhost:3000/api/users/profile/${userId}`);
            // Verify token before redirecting
            const verifyResponse = await fetch(`http://localhost:3000/api/users/profile/${userId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            console.log('Profile verification status:', verifyResponse.status);

            if (verifyResponse.ok) {
                const userData = await verifyResponse.json();
                console.log('Profile verification response:', userData);

                // Store complete user data
                localStorage.setItem('userData', JSON.stringify({
                    user: userData.data.user,
                    tokenInfo: userData.data.tokenInfo
                }));

                window.location.href = 'popup.html';
            } else {
                const errorText = await verifyResponse.text();
                console.error('Profile verification failed:', {
                    status: verifyResponse.status,
                    error: errorText
                });
                showError('Authentication failed. Please try again.');
                // Clear storage on verification failure
                localStorage.removeItem('userToken');
                localStorage.removeItem('userEmail');
                localStorage.removeItem('userId');
            }
        } else {
            console.error('Login failed:', {
                status: response.status,
                message: data.message,
                success: data.success
            });

            // Handle specific error cases
            switch (response.status) {
                case 401:
                    showError('Invalid email or password. Please try again.');
                    break;
                case 404:
                    showError('Login service not found. Please try again later.');
                    break;
                case 500:
                    showError('Server error. Please try again later.');
                    break;
                default:
                    showError(data.message || 'Login failed. Please try again.');
            }
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('Network error. Please check your connection and try again.');
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
    const token = localStorage.getItem('userToken');
    const userId = localStorage.getItem('userId');
    
    if (!token || !userId) {
        throw new Error('No authentication token or user ID found');
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