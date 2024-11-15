import React, { useState, useEffect } from 'react';
import velocitylogo from "../assets/velocitylogo.png";
import { Link } from 'react-router-dom';
import ProfilePage from './ProfilePage';

const Login = ({setIsLoggedIn}) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showTokenDetails, setShowTokenDetails] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({
    email: '',
    password: '',
  });

  // Session management
  const SESSION_DURATION = 60 * 1000; // 1 minute in milliseconds

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
        // setMessage(<span style={{ color: 'red' }}>Session expired. Please log in again.</span>);
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
        // setMessage(<span style={{ color: 'red' }}>Session expired. Please log in again.</span>);
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
        setIsLoggedIn(true);

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
    <div className="min-h-screen bg-[#0C0C0C] sm:bg-black absolute h-full w-full flex justify-center items-center z-30 flex-col sm:flex-row sm:gap-0 gap-12" >
      <div className="bg-[#0C0C0C] sm:bg-black/60 order-2 sm:order-1 rounded-lg shadow-sm py-6 px-6 sm:px-36 sm:w-1/2 w-full">
        <h2 className="text-left text-3xl sm:text-[42px] font-normal text-primary mb-4">Welcome back</h2>
        <h2 className="text-left text-[16px] font-normal text-[#808080] mb-10">Welcome back! Please enter your details.</h2>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-gray-600 mb-2">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                required
                className="w-full py-2 px-4 border bg-transparent border-[#808080] rounded-lg focus:outline-none text-primary focus:none"
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
              <label htmlFor="password" className="block text-sm font-semibold text-gray-600 mb-2">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                required
                className="w-full py-2 px-4 border bg-transparent border-[#808080] rounded-lg focus:outline-none text-primary focus:none"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => handleFieldChange('password', e.target.value)}
                disabled={isLoading}
              />
              {fieldErrors.password && (
                <p className="text-red-500 text-xs mt-1">{fieldErrors.password}</p>
              )}
            </div>

            <div className='my-3 flex justify-center'>
              <span className='font-[Inter] text-sm text-[#008ACB] hover:text-[#4bb8eb] cursor-pointer'>Forgot password?</span>
            </div>

            <div className='w-full flex justify-center'>
              <button 
              className='bg-[#008ACB] text-primary rounded-md w-full py-3'
                click={handleSubmit} 
                content={isLoading ? "Signing in..." : "Sign in"} 
                disabled={isLoading} 
              >Sign in</button>
            </div>
          </div>

          <div id="message" className="mt-4 text-center text-sm text-gray-600">
            {message}
          </div>
        </form>

        <div className="mt-4 text-center">
          <p className="text-sm bg-gradient-text">
            Don't have an account?{' '}
            <Link to="/register" className="text-[#008ACB] hover:text-[#4bb8eb]">
              Sign up
            </Link>
          </p>
        </div>
      </div>
      <div className="flex justify-center order-1 sm:order-2 items-center w-1/2 h-auto sm:h-screen bg-[#0C0C0C]">
      <Link
            to="/"
            className={'flex items-center space-x-3 sm:w-auto w-auto absolute top-16 right-16 '}
          >
            <img
              src={velocitylogo}
              className="h-10 sm:h-14"
              alt="Velocity Logo"
            />
          </Link>
      <div className="relative">
        {/* Blue Circle */}
        <div className="w-24 h-24 sm:w-64 sm:h-64 bg-blue-500 rounded-full"></div>

        {/* Backdrop blur effect on the lower half */}
        <div className="absolute top-1/2 sm:left-[-40px] w-40 h-20 left-[-35px] sm:w-96 sm:h-40 backdrop-blur-md bg-[#0C0C0C]/40"></div>
      </div>
    </div>
    </div>
  );
};

export default Login;