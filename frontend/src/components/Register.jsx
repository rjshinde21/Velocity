import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import velocitylogo from "../assets/velocitylogo.png";
import ThreeDLogo from './3dLogo/ThreeDLogo';
import supabase from '../config/supabaseClient';
import googleLogo from '../assets/googleLogo.png';


const Register = () => {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [animate, setAnimate] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [showSpinner, setShowSpinner] = useState(false);
  const authInProgressRef = useRef(false);

  useEffect(() => {
    let mounted = true;

    const processGoogleAuth = async (session) => {
      if (!session?.user || !mounted) return;

      try {
        setIsLoading(true);
        setMessage(<span style={{ color: '#2563eb' }}>Processing registration...</span>);

        const apiResponse = await fetch('http://127.0.0.1:3000/api/users/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: session.user.user_metadata?.full_name || session.user.email,
            email: session.user.email,
            googleId: session.user.id,
            avatar: session.user.user_metadata?.avatar_url
          })
        });

        if (!mounted) return;

        const data = await apiResponse.json();
        console.log('Register API Response:', data);

        if (apiResponse.ok) {
          localStorage.setItem('token', data.data.token);
          localStorage.setItem('userId', data.data.user.id);
          localStorage.setItem('user', JSON.stringify(data.data.user));
          localStorage.setItem('loginTime', new Date().getTime().toString());
          navigate('/profile');
        } else if (apiResponse.status === 409) {
          navigate('/login');
        } else {
          throw new Error(data.message || 'Registration failed');
        }
      } catch (error) {
        console.error('Registration error:', error);
        if (mounted) {
          setMessage(<span style={{ color: 'red' }}>Failed to complete registration. Please try again.</span>);
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    // Check for existing session immediately
    const checkExistingSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.user && mounted) {
        await processGoogleAuth(session);
      }
    };
    checkExistingSession();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      console.log('Auth event:', event);
      if (event === 'SIGNED_IN') {
        await processGoogleAuth(session);
      }
    });

    // Cleanup
    return () => {
      mounted = false;
      subscription?.unsubscribe();
    };
  }, [navigate]);

  
  
  const validateField = (field, value) => {
    let error = '';
    switch (field) {
      case 'name':
        if (!value.trim()) error = 'Name is required';
        else if (value.length < 2) error = 'Name must be at least 2 characters';
        break;
      case 'email':
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!value) error = 'Email is required';
        else if (!emailRegex.test(value)) error = 'Please enter a valid email';
        break;
      case 'password':
        if (!value) error = 'Password is required';
        else if (value.length < 6) error = 'Password must be at least 6 characters';
        break;
      case 'confirmPassword':
        if (!value) error = 'Please confirm your password';
        else if (value !== password) error = 'Passwords do not match';
        break;
      default:
        break;
    }
    return error;
  };

  const handleFieldChange = (field, value) => {
    switch (field) {
      case 'name':
        setName(value);
        break;
      case 'email':
        setEmail(value);
        break;
      case 'password':
        setPassword(value);
        if (confirmPassword) {
          setFieldErrors(prev => ({
            ...prev,
            confirmPassword: value !== confirmPassword ? 'Passwords do not match' : ''
          }));
        }
        break;
      case 'confirmPassword':
        setConfirmPassword(value);
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

    const errors = {
      name: validateField('name', name),
      email: validateField('email', email),
      password: validateField('password', password),
      confirmPassword: validateField('confirmPassword', confirmPassword)
    };

    setFieldErrors(errors);

    if (Object.values(errors).some(error => error)) {
      setMessage(<span style={{ color: 'red' }}>Please fix the errors before submitting</span>);
      return;
    }

    setIsLoading(true);
    setMessage(<span style={{ color: '#2563eb' }}>Processing registration...</span>);

    try {
      const response = await fetch('http://127.0.0.1:3000/api/users/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          name,
          email,
          password,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(<span style={{ color: 'green' }}>Registration successful! Redirecting...</span>);
        setTimeout(() => navigate('/login'), 2000);
      } else {
        switch (response.status) {
          case 400:
            setMessage(<span style={{ color: 'red' }}>Error: {data.message || 'Invalid input data'}</span>);
            break;
          case 409:
            setMessage(<span style={{ color: 'red' }}>Email already registered. Please login instead.</span>);
            break;
          default:
            setMessage(<span style={{ color: 'red' }}>Error: {data.message || 'Registration failed'}</span>);
        }
      }
    } catch (error) {
      console.error('Registration error:', error);
      setMessage(<span style={{ color: 'red' }}>Network error. Please try again.</span>);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignUp = async (e) => {
    e.preventDefault();
    setMessage(<span style={{ color: '#2563eb' }}>Connecting to Google...</span>);
    setIsLoading(true);

    try {
      await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/register`,
          scopes: 'email profile',
        }
      });
    } catch (error) {
      console.error('Google Sign Up Error:', error);
      setMessage(<span style={{ color: 'red' }}>Failed to connect with Google. Please try again.</span>);
      setIsLoading(false);
    }
  };

  if (showSpinner) {
    return (
      <div className="min-h-screen bg-[#0C0C0C] flex items-center justify-center">
        <div className="text-primary">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
          <p className="mt-4">Processing Google Sign Up...</p>
        </div>
      </div>
    );
  }

  
  return (
    <div className="min-h-screen bg-[#0C0C0C] sm:bg-black fixed h-full w-full flex justify-center items-center sm:flex-row flex-col z-30 sm:gap-0 gap-12">
      <div className="bg-[#0C0C0C] sm:bg-black/60 order-2 sm:order-1 rounded-lg shadow-sm px-6 sm:px-36 sm:w-1/2 w-full" style={{zIndex: 2}}>
        <h2 className="text-left text-3xl sm:text-[42px] font-normal text-primary mb-8">Create an account</h2>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            {/* Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-semibold text-gray-600 mb-2">Name</label>
              <input
                type="text"
                id="name"
                name="name"
                required
                className="w-full py-2 px-4 border bg-transparent border-[#808080] rounded-lg focus:outline-none text-primary focus:none"
                placeholder="Enter your name"
                value={name}
                onChange={(e) => handleFieldChange('name', e.target.value)}
              />
              {fieldErrors.name && (
                <p className="text-red-500 text-xs mt-1">{fieldErrors.name}</p>
              )}
            </div>

            {/* Email */}
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
              />
              {fieldErrors.email && (
                <p className="text-red-500 text-xs mt-1">{fieldErrors.email}</p>
              )}
            </div>

            {/* Password */}
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
              />
              {fieldErrors.password && (
                <p className="text-red-500 text-xs mt-1">{fieldErrors.password}</p>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-semibold text-gray-600 mb-2">Confirm Password</label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                required
                className="w-full py-2 px-4 border bg-transparent border-[#808080] rounded-lg focus:outline-none text-primary focus:none"
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={(e) => handleFieldChange('confirmPassword', e.target.value)}
              />
              {fieldErrors.confirmPassword && (
                <p className="text-red-500 text-xs mt-1">{fieldErrors.confirmPassword}</p>
              )}
            </div>

            {/* Register Button */}
            <div className='w-full flex justify-center'>
              <button 
                className={`bg-[#008ACB] text-primary rounded-md w-full py-3 mt-2 ${
                  isLoading ? 'opacity-50 cursor-not-allowed' : ''
                }`}
                type="submit"
                disabled={isLoading}
              >
                {isLoading ? 'Processing...' : 'Register'}
              </button>
            </div>

            {/* Google Sign Up Button */}
            <div className='w-full flex justify-center'>
              <button 
                onClick={handleGoogleSignUp}
                className={`bg-[#000000] border-[#989898] border text-primary rounded-md w-full py-3 flex gap-2 justify-center items-center ${
                  isLoading ? 'opacity-50 cursor-not-allowed' : ''
                }`}
                disabled={isLoading}
              >
                <img src={googleLogo} alt="Google" />
                {isLoading ? 'Processing...' : 'Sign up with Google'}
              </button>
            </div>
          </div>

          {/* Message Area */}
          {message && (
            <div className="mt-4 text-center text-sm text-gray-600">
              {message}
            </div>
          )}
        </form>

        {/* Link to Login */}
        <div className="mt-4 text-center">
          <p className="text-sm bg-gradient-text">
            Already have an account?{' '}
            <Link to="/login" className="text-[#008ACB] hover:text-[#4bb8eb]">
              Log In
            </Link>
          </p>
        </div>
      </div>

      {/* Logo and 3D Animation Section */}
      <div className="flex justify-center order-1 sm:order-2 items-center w-1/2 h-[20vh] sm:h-screen bg-[#0C0C0C]">
        <Link
          to="/"
          className={'flex items-center space-x-3 sm:w-auto w-auto absolute top-16 right-16'}
        >
          <img
            src={velocitylogo}
            className="h-10 sm:h-14"
            alt="Velocity Logo"
          />
        </Link>

        <div className="relative">
          <ThreeDLogo />
        </div>
      </div>
    </div>
  );
};

export default Register;
