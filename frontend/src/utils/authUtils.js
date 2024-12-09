// utils/authUtils.js
const SESSION_DURATION = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

export const setAuthData = (userData, authInfo) => {
  try {
    // Store auth data with 'shared' prefix for cross-platform access
    localStorage.setItem('token', authInfo.token);
    localStorage.setItem('sharedUserId', authInfo.userId);
    localStorage.setItem('sharedUser', JSON.stringify(userData));
    localStorage.setItem('sharedLoginTime', new Date().getTime().toString());

    // Dispatch event for extension to detect
    window.dispatchEvent(new Event('sharedAuthChanged'));
  } catch (error) {
    console.error('Error setting auth data:', error);
    clearSharedAuthData();
  }
};

export const getSharedAuthData = () => {
  try {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('sharedUserId');
    const userData = JSON.parse(localStorage.getItem('sharedUser') || 'null');
    const loginTime = localStorage.getItem('sharedLoginTime');

    return {
      token,
      userId,
      userData,
      loginTime
    };
  } catch (error) {
    console.error('Error getting auth data:', error);
    return null;
  }
};

export const clearSharedAuthData = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('sharedUserId');
  localStorage.removeItem('sharedUser');
  localStorage.removeItem('sharedLoginTime');
  localStorage.removeItem('sharedFirebaseUser');
  
  // Dispatch event for extension to detect
  window.dispatchEvent(new Event('sharedAuthChanged'));
};

export const isSharedSessionValid = () => {
  const loginTime = localStorage.getItem('sharedLoginTime');
  if (!loginTime) return false;
  
  const currentTime = new Date().getTime();
  const timeSinceLogin = currentTime - parseInt(loginTime, 10);
  return timeSinceLogin < SESSION_DURATION;
};

export const verifySharedToken = async () => {
  const { token, userId } = getSharedAuthData();
  
  if (!token || !userId) return false;
  
  try {
    const response = await fetch(`https://thinkvelocity.in/api/api/users/profile/${userId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    return response.ok;
  } catch (error) {
    console.error('Token verification failed:', error);
    return false;
  }
};

export const isAuthenticated = () => {
  return isSharedSessionValid() && getSharedAuthData().token;
};