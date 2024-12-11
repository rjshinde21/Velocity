import { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { GoogleAuthProvider, signInWithPopup } from 'firebase/auth';
import { auth } from '../config/firebaseConfig';
import { setAuthData } from '../utils/authUtils';
import velocitylogo from "../assets/velocitylogo.png";
import googleLogo from '../assets/googleLogo.png';
import ThreeDLogo from './3dLogo/ThreeDLogo';

const Register = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [referralCode, setReferralCode] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    referralCode: ''
  });

  // Extract referral code from URL if present
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const refCode = params.get('ref');
    if (refCode) {
      setReferralCode(refCode);
    }
  }, [location]);

  const validateField = (field, value) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    let error = '';
    switch (field) {
      case 'name':
        if (!value.trim()) error = 'Name is required';
        else if (value.length < 2) error = 'Name must be at least 2 characters';
        break;
      case 'email':
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
      case 'referralCode':
        if (value && value.length !== 10) error = 'Invalid referral code';
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
      case 'referralCode':
        setReferralCode(value.toUpperCase());
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

  const applyReferral = async (userId, token) => {
    try {
      const response = await fetch('https://thinkvelocity.in/api/api/referral/apply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          referral_code: referralCode,
          new_user_id: userId
        })
      });

      if (!response.ok) {
        console.warn('Referral application failed:', await response.text());
        setMessage(<span style={{ color: 'orange' }}>Account created, but referral bonus could not be applied</span>);

      }
    } catch (error) {
      console.error('Error applying referral:', error);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage('');
  
    const errors = {
      name: validateField('name', name),
      email: validateField('email', email),
      password: validateField('password', password),
      confirmPassword: validateField('confirmPassword', confirmPassword),
      referralCode: validateField('referralCode', referralCode)
    };
  
    setFieldErrors(errors);
  
    if (Object.values(errors).some(error => error)) {
      setMessage(<span style={{ color: 'red' }}>Please fix the errors before submitting</span>);
      return;
    }
  
    setIsLoading(true);
    setMessage(<span style={{ color: '#2563eb' }}>Processing registration...</span>);
  
    try {
      const response = await fetch('https://thinkvelocity.in/api/api/users/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          email,
          password,
        }),
      });
  
      const data = await response.json();

      console.log("registered user?:"+response.ok);
      if (response.ok) {
        // Store user data in localStorage
        localStorage.setItem('token', data.data.token);
        localStorage.setItem('userId', data.data.user.id);
        localStorage.setItem('userEmail', data.data.user.email);
        localStorage.setItem('userName', data.data.user.username || name);
        
        // Apply referral code if provided
        if (referralCode) {
          await applyReferral(data.data.user.id, data.data.token);
        }
  
        setMessage(<span style={{ color: 'green' }}>Registration successful! Redirecting...</span>);
        setTimeout(() => navigate('/profile'), 2000);
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
    setIsLoading(true);
    setMessage(<span style={{ color: '#2563eb' }}>Connecting to Google...</span>);
  
    try {
      const provider = new GoogleAuthProvider();
      const result = await signInWithPopup(auth, provider);
      const user = result.user;
  
      const apiResponse = await fetch('https://thinkvelocity.in/api/api/users/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: user.displayName || user.email,
          email: user.email,
          googleId: user.uid,
          avatar: user.photoURL
        })
      });
  
      const data = await apiResponse.json();
  
      if (apiResponse.ok) {
        // Store user data in localStorage
        localStorage.setItem('token', data.data.token);
        localStorage.setItem('userId', data.data.user.id);
        localStorage.setItem('userEmail', data.data.user.email);
        localStorage.setItem('userName', data.data.user.username || user.displayName || user.email);
        
        // Apply referral code if provided
        if (referralCode) {
          await applyReferral(data.data.user.id, data.data.token);
        }
  
        setMessage(<span style={{ color: 'green' }}>Registration successful! Redirecting...</span>);
        setTimeout(() => navigate('/profile'), 1000);
      } else if (apiResponse.status === 409) {
        setMessage(<span style={{ color: 'orange' }}>Account exists. Redirecting to login...</span>);
        setTimeout(() => navigate('/login'), 2000);
      } else {
        throw new Error(data.message || 'Registration failed');
      }
    } catch (error) {
      console.error('Google Sign Up Error:', error);
      setMessage(<span style={{ color: 'red' }}>Failed to connect with Google. Please try again.</span>);
    } finally {
      setIsLoading(false);
    }
  };
    return (
      <div className="min-h-screen bg-[#0C0C0C] sm:bg-black fixed h-full w-full flex justify-center items-center sm:flex-row flex-col z-30 sm:gap-0 gap-12">
      {/* Form Section */}
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
            <div>
              <label htmlFor="referralCode" className="block text-sm font-semibold text-gray-600 mb-2">
                Referral Code (Optional)
              </label>
              <input
                type="text"
                id="referralCode"
                name="referralCode"
                className="w-full py-2 px-4 border bg-transparent border-[#808080] rounded-lg focus:outline-none text-primary focus:none"
                placeholder="Enter referral code"
                value={referralCode}
                onChange={(e) => handleFieldChange('referralCode', e.target.value)}
              />
              {fieldErrors.referralCode && (
                <p className="text-red-500 text-xs mt-1">{fieldErrors.referralCode}</p>
              )}
            </div>
            {/* Register Button */}
            <div className='w-full flex justify-center'>
              <button 
                className={`bg-[#008ACB] text-primary rounded-md w-full py-3 mt-2 ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
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
                className={`bg-[#000000] border-[#989898] border text-primary rounded-md w-full py-3 flex gap-2 justify-center items-center ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
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
      <div className="flex justify-center order-1 sm:order-2 items-center w-full sm:w-1/2 sm:h-screen bg-[#0C0C0C]">
        <Link
          to="/"
          className={'flex items-center space-x-3 sm:w-auto w-auto absolute top-16 right-16 hidden sm:block'}
        >
          <img
            src={velocitylogo}
            className="h-10 sm:h-14"
            alt="Velocity Logo"
          />
        </Link>
    
        <div className="relative hidden sm:block">
          <ThreeDLogo />
        </div>
      </div>
    </div>    
  );
};

export default Register;
