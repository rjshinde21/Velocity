import React, { useState } from 'react';
import GetStartedBtn from './GetStartedBtn';
import { Link, useNavigate } from 'react-router-dom';
import bg from "../assets/mainbg.png"
import TokenDetails from './TokenDetails';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showTokenDetails, setShowTokenDetails] = useState(false);
  const navigate = useNavigate(); // Add this line to use navigation
  const [fieldErrors, setFieldErrors] = useState({
    email: '',
    password: '',
  });

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
      console.log("data recvd:"+data.data.token);
      if (response.ok) {
        
        // Save user data and token
        console.log("setting token:"+data.data.token);
        localStorage.setItem('token', data.data.token);
        localStorage.setItem('userId', data.data.userId);
        localStorage.setItem('userEmail', data.data.email);
        console.log("token set:"+data.token);
        setMessage(<span style={{ color: 'green' }}>Login successful! Redirecting...</span>);
        
        // Navigate after a short delay
        setTimeout(() => {
          setShowTokenDetails(true);
          //navigate('/token-details');
        }, 1000);
      } else {
        // Handle different error cases
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
    return <TokenDetails />;
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
            {/* Email */}
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

            {/* Password */}
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

            {/* Submit Button */}
            <div className='w-full flex justify-center'>
              <GetStartedBtn 
                click={handleSubmit} 
                content={isLoading ? "Signing in..." : "Sign in"} 
                disabled={isLoading} 
              />
            </div>
          </div>

          {/* Message Area */}
          <div id="message" className="mt-4 text-center text-sm text-gray-600">
            {message}
          </div>
        </form>

        {/* Link to Register */}
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