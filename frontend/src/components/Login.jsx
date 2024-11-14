import React, { useState, useEffect } from 'react';
import GetStartedBtn from './GetStartedBtn';
import { Link, useNavigate } from 'react-router-dom';
import bg from "../assets/mainbg.png";
import TokenDetails from './TokenDetails';
import ProfilePage from './ProfilePage';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showTokenDetails, setShowTokenDetails] = useState(false);
  const navigate = useNavigate();
  const [fieldErrors, setFieldErrors] = useState({
    email: '',
    password: '',
  });

  // Session management
  const SESSION_DURATION = 60 * 1000; // 1 day in milliseconds

  const handleReLogin = async (email, password) => {
    try {
      const response = await fetch('http://127.0.0.1:3000/api/users/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        const data = await response.json();
        const currentTime = new Date().getTime();

        // Save session data again
        localStorage.setItem('token', data.data.token);
        localStorage.setItem('userId', data.data.user.id);
        localStorage.setItem('userEmail', email);
        localStorage.setItem('loginTime', currentTime.toString());
        return true; // Re-login successful
      } else {
        console.error("Re-login failed:", await response.text());
        return false; // Re-login failed
      }
    } catch (error) {
      console.error("Network error during re-login:", error);
      return false; // Network or other error
    }
  };

  const checkAndClearSession = async () => {
    const loginTime = localStorage.getItem('loginTime');
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('userId');
    const savedEmail = localStorage.getItem('userEmail');
  
    if (loginTime && token && userId) {
      const currentTime = new Date().getTime();
      const timeSinceLogin = currentTime - parseInt(loginTime, 10);
  
      if (timeSinceLogin > SESSION_DURATION) {
        // Session expired, clear session and attempt re-login
        clearSessionData();
  
        // Attempt re-login if saved credentials are available
        if (savedEmail && password) {
          const reLoginSuccessful = await handleReLogin(savedEmail, password);
          if (reLoginSuccessful) {
            setShowTokenDetails(true);
            return false; // Session refreshed
          }
        }
        return true; // Session expired, re-login failed
      } else {
        // Session is still valid
        setShowTokenDetails(true);
        return false;
      }
    }
    return true; // No session exists
  };

  const clearSessionData = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('loginTime');
    setShowTokenDetails(false);
    navigate('/login');
  };

  const setupSessionExpirationCheck = () => {
    const loginTime = localStorage.getItem('loginTime');
    if (loginTime) {
      const currentTime = new Date().getTime();
      const timeSinceLogin = currentTime - parseInt(loginTime, 10);
      const timeRemaining = SESSION_DURATION - timeSinceLogin;

      if (timeRemaining > 0) {
        const timeoutId = setTimeout(() => {
          clearSessionData();
          // setMessage(<span style={{ color: 'red' }}>Session expired. Please log in again.</span>);
        }, timeRemaining);

        return () => clearTimeout(timeoutId);
      } else {
        clearSessionData();
      }
    }
  };

  useEffect(() => {
    const checkSession = async () => {
      const sessionExpired = await checkAndClearSession();
      if (sessionExpired) {
        setMessage(<span style={{ color: 'red' }}>Session expired. Please log in again.</span>);
      }
    };

    checkSession();
    const cleanup = setupSessionExpirationCheck();
    return () => {
      if (cleanup) cleanup();
    };
  }, []);

  useEffect(() => {
    const intervalId = setInterval(async () => {
      const sessionExpired = await checkAndClearSession();
      if (sessionExpired) {
        setMessage(<span style={{ color: 'red' }}>Session expired. Please log in again.</span>);
      }
    }, 5000);

    return () => clearInterval(intervalId);
  }, []);

  const validateField = (field, value) => {
    let error = '';
    switch (field) {
      case 'email':
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!value) error = 'Email is required';
        else if (!emailRegex.test(value)) error = 'Please enter a valid email';
        break;
      case 'password':
        if (!value) error = 'Password is required';
        else if (value.length < 6) error = 'Password must be at least 6 characters';
        break;
      default:
        break;
    }
    return error;
  };

  const handleFieldChange = (field, value) => {
    switch (field) {
      case 'email':
        setEmail(value);
        break;
      case 'password':
        setPassword(value);
        break;
      default:
        break;
    }

    const error = validateField(field, value);
    setFieldErrors(prev => ({
      ...prev,
      [field]: error
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage('');

    // Validate fields
    const errors = {
      email: validateField('email', email),
      password: validateField('password', password),
    };

    setFieldErrors(errors);

    if (Object.values(errors).some(error => error)) {
      setMessage(<span style={{ color: 'red' }}>Please fix the errors before submitting</span>);
      return;
    }

    setIsLoading(true);
    setMessage(<span style={{ color: '#2563eb' }}>Processing login...</span>);

    try {
      const response = await fetch('http://127.0.0.1:3000/api/users/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          email,
          password
        }),
      });

      const data = await response.json();

      if (response.ok) {
        const currentTime = new Date().getTime();
        
        // Save session data
        localStorage.setItem('token', data.data.token);
        localStorage.setItem('userId', String(data.data.user.id)); // Ensure userId is stored as string
        localStorage.setItem('userEmail', email);
        localStorage.setItem('loginTime', currentTime.toString());

        setMessage(<span style={{ color: 'green' }}>Login successful! Redirecting...</span>);
        
        setupSessionExpirationCheck();
        
        setTimeout(() => {
          setShowTokenDetails(true);
        }, 1000);
      } else {
        switch (response.status) {
          case 400:
            setMessage(<span style={{ color: 'red' }}>Invalid email or password format</span>);
            break;
          case 401:
            setMessage(<span style={{ color: 'red' }}>Invalid email or password</span>);
            break;
          case 404:
            setMessage(<span style={{ color: 'red' }}>Account not found</span>);
            break;
          default:
            setMessage(<span style={{ color: 'red' }}>{data.message || 'Login failed'}</span>);
        }
      }
    } catch (error) {
      console.error('Login error:', error);
      setMessage(
        <span style={{ color: 'red' }}>
          Network error. Please check your connection and try again.
        </span>
      );
    } finally {
      setIsLoading(false);
    }
  };

  if (showTokenDetails) {
    return <ProfilePage />;
  }

  return (
    <div className="min-h-screen backdrop-blur-lg absolute h-full w-full flex justify-center items-center z-10" 
      style={{
        backgroundImage: `url(${bg})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}>
      <div className="bg-black/60 rounded-lg shadow-sm p-6 max-w-md w-full mx-auto">
        <h2 className="text-center text-2xl font-bold bg-gradient-text mb-4">Sign into your Account</h2>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-gray-600">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                required
                className="w-full p-2 border-b bg-transparent rounded-lg focus:outline-none text-primary focus:none"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => handleFieldChange('email', e.target.value)}
                disabled={isLoading}
              />
              {fieldErrors.email && (
                <p className="text-red-500 text-xs mt-1">{fieldErrors.email}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-gray-600">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                required
                className="w-full p-2 border-b bg-transparent rounded-lg focus:outline-none text-primary focus:none"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => handleFieldChange('password', e.target.value)}
                disabled={isLoading}
              />
              {fieldErrors.password && (
                <p className="text-red-500 text-xs mt-1">{fieldErrors.password}</p>
              )}
            </div>

            <div className='w-full flex justify-center'>
              <GetStartedBtn 
                click={handleSubmit} 
                content={isLoading ? "Signing in..." : "Sign in"} 
                disabled={isLoading} 
              />
            </div>
          </div>

          <div id="message" className="mt-4 text-center text-sm text-gray-600">
            {message}
          </div>
        </form>

        <div className="mt-4 text-center">
          <p className="text-sm bg-gradient-text">
            Don't have an account?{' '}
            <Link to="/register" className="text-blue-600 hover:text-blue-800">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;