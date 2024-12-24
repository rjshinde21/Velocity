import React, { useState, useEffect,useCallback   } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { GoogleAuthProvider, signInWithPopup } from 'firebase/auth';
import Particles from "react-tsparticles";
import { loadFull } from "tsparticles";
import { auth } from '../config/firebaseConfig';
import velocitylogo from "../assets/velocitylogo.png";
import googleLogo from '../assets/googleLogo.png';
import ThreeDLogo from './3dLogo/ThreeDLogo';
import Analytics from '../config/analytics';

import {setAuthData} from '../utils/authUtils'
const Login = ({setIsLoggedIn}) => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({
    email: '',
    password: '',
  });

  
  const particlesInit = useCallback(async (engine) => {
    await loadFull(engine);
  }, []);

  const particlesLoaded = useCallback(async (container) => {
    console.log("Particles loaded:", container);
  }, []);

  const particlesConfig = {
    autoPlay: true,
    background: {
      color: {
        value: "#000000"
      },
      opacity: 1
    },
    fullScreen: {
      enable: false,
    },
    detectRetina: true,
    fpsLimit: 120,
    particles: {
      color: {
        value: "#ffffff"
      },
      links: {
        color: "#ffffff",
        distance: 150,
        enable: true,
        opacity: 0.2,
        width: 1
      },
      move: {
        direction: "none",
        enable: true,
        outModes: {
          default: "bounce"
        },
        random: true,
        speed: 1,
        straight: false
      },
      number: {
        density: {
          enable: true,
          area: 800
        },
        value: 30
      },
      opacity: {
        value: 0.3
      },
      shape: {
        type: "circle"
      },
      size: {
        value: { min: 1, max: 3 }
      }
    }
  };
  useEffect(() => {
    // Check for existing session
    const checkSession = async () => {
      const storedToken = localStorage.getItem('token');
      const storedUser = localStorage.getItem('firebaseUser');
      
      if (storedToken && storedUser) {
        try {
          const verifyResponse = await fetch('https://thinkvelocity.in/api/api/users/verify-token', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${storedToken}`,
              'Content-Type': 'application/json'
            }
          });
  
          if (verifyResponse.ok) {
            setIsLoggedIn(true);
            navigate('/profile');
            return;
          }
        } catch (error) {
          console.error('Session verification failed:', error);
        }
      }
    };
  
    checkSession();
  }, [navigate, setIsLoggedIn]);
  



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
      const response = await fetch('https://thinkvelocity.in/api/api/users/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();
      console.log("login api data:"+data);
      if (response.ok) {
        localStorage.setItem('authMethod', 'email');
        Analytics.track('User Login', {
          method: 'email',
          timestamp: new Date()
        });
        Analytics.identify(data.data.user.id);
        Analytics.setUserProperties({
          email: data.data.user.email,
          username: data.data.user.name
          // other user details
        });
        handleSuccessfulLogin(data.data.user, data.data.token);
      } else {
        throw new Error(data.message || 'Login failed');
      }
    } catch (error) {
      console.error('Login error:', error);
      setMessage(<span style={{ color: 'red' }}>Invalid email or password</span>);
    } finally {
      setIsLoading(false);
    }
  };
  


  const handleGoogleSignIn = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage(<span style={{ color: '#2563eb' }}>Connecting to Google...</span>);
  
    try {
      // 1. Sign in with Google
      const provider = new GoogleAuthProvider();
      const result = await signInWithPopup(auth, provider);
      const user = result.user;
      
      // 2. Call your API
      const response = await fetch('https://thinkvelocity.in/api/api/users/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: user.email,
          googleId: user.uid,
        })
      });
  
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem('authMethod', 'google');
        Analytics.track('User Login', {
          method: 'google',
          timestamp: new Date()
        });
        Analytics.identify(data.data.user.id);
        Analytics.setUserProperties({
          email: data.data.user.email,
          username: data.data.user.name
          // other user details
        });
        //handleSuccessfulLogin(data.data.user, data.data.token);
      }
    
      if (!response.ok) {
        throw new Error(data.message || 'Login failed');
      }
  
      // 3. Store everything at once
      const authData = {
        token: data.data.token,
        user: data.data.user,
        firebase: {
          uid: user.uid,
          email: user.email
        }
      };
  
      // Store everything in one go
      localStorage.setItem('token', authData.token);
      localStorage.setItem('userId', authData.user.id);
      localStorage.setItem('userEmail', authData.user.email);
      localStorage.setItem('userName', authData.user.name);
      localStorage.setItem('firebaseUser', JSON.stringify(authData.firebase));
  
      // 4. Update app state and navigate
      setIsLoggedIn(true);
      navigate('/profile', { replace: true });
  
    } catch (error) {
      console.error('Login error:', error);
      setMessage(<span style={{ color: 'red' }}>Login failed. Please try again.</span>);
      // Clean up on error
      localStorage.clear();
      await auth.signOut();
    } finally {
      setIsLoading(false);
    }
  };
  
  
  const handleSuccessfulLogin = (userData, token) => {
    console.log("Storing login data for:", userData.email);
    
    // Store all necessary data
    localStorage.setItem('token', token);
    localStorage.setItem('userId', userData.id);
    localStorage.setItem('userEmail', userData.email);
    localStorage.setItem('userName', userData.name);
    // Store Firebase user data
    if (auth.currentUser) {
      localStorage.setItem('firebaseUser', JSON.stringify({
        uid: auth.currentUser.uid,
        email: auth.currentUser.email
      }));
    }
    
    setIsLoggedIn(true);
    setMessage(<span style={{ color: 'green' }}>Login successful!</span>);
    navigate('/profile');  // Remove setTimeout and navigate immediately
  };

  

  // if (showTokenDetails) {
  //   return <ProfilePage />;
  // }

  return (
    <div className="relative min-h-screen">
    {/* Full screen particles */}
    <div className="fixed inset-0">
      <Particles
        id="tsparticles"
        init={particlesInit}
        loaded={particlesLoaded}
        options={particlesConfig}
        className="w-full h-full"
      />
    </div>

    {/* Content overlay */}
    <div className="relative z-10 flex min-h-screen">
      {/* Form section */}
      <div className="w-full lg:w-[45%] px-4 sm:px-8 lg:px-12 xl:px-24 2xl:px-36 
        flex flex-col justify-center">
          <div className="lg:hidden w-full flex justify-left mt-6 sm:mt-8">
            <Link to="/">
              <img 
                src={velocitylogo} 
                className="h-8 sm:h-10 transition-all duration-300" 
                alt="Velocity Logo" 
              />
            </Link>
          </div>

          <div className="bg-transparent rounded-lg shadow-sm max-w-xl mx-auto w-full py-6 sm:py-8 lg:py-10">
            {/* Form Header */}
            <div className="mb-6 sm:mb-8 lg:mb-10">
              <h2 className="text-left text-2xl sm:text-3xl lg:text-[42px] font-normal text-primary 
                mb-2 sm:mb-3 lg:mb-4">
                Welcome back!
              </h2>
              <h2 className="text-left text-sm sm:text-base text-[#808080]">
                Please enter your details.
              </h2>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-5 lg:space-y-6">
              {/* Email Input */}
              <div>
                <label htmlFor="email" className="block text-sm font-semibold text-gray-600 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  className="w-full py-2.5 sm:py-3 lg:py-3.5 px-4 sm:px-5 
                    border bg-transparent border-[#808080] rounded-lg 
                    focus:outline-none text-primary text-sm sm:text-base
                    transition-all duration-300 hover:border-[#a0a0a0] 
                    focus:border-[#008ACB]"
                  value={email}
                  onChange={(e) => handleFieldChange('email', e.target.value)}
                  disabled={isLoading}
                />
                {fieldErrors.email && (
                  <p className="text-red-500 text-xs mt-1">{fieldErrors.email}</p>
                )}
              </div>

              {/* Password Input */}
              <div>
                <label htmlFor="password" className="block text-sm font-semibold text-gray-600 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  id="password"
                  className="w-full py-2.5 sm:py-3 lg:py-3.5 px-4 sm:px-5 
                    border bg-transparent border-[#808080] rounded-lg 
                    focus:outline-none text-primary text-sm sm:text-base
                    transition-all duration-300 hover:border-[#a0a0a0] 
                    focus:border-[#008ACB]"
                  value={password}
                  onChange={(e) => handleFieldChange('password', e.target.value)}
                  disabled={isLoading}
                />
                {fieldErrors.password && (
                  <p className="text-red-500 text-xs mt-1">{fieldErrors.password}</p>
                )}
              </div>

              {/* Forgot Password */}
              <div className="flex justify-center py-1 sm:py-2">
                <span className="font-[Inter] text-sm sm:text-base text-[#008ACB] 
                  hover:text-[#4bb8eb] cursor-pointer transition-colors">
                  Forgot password?
                </span>
              </div>

              {/* Login Buttons */}
              <div className="space-y-3 sm:space-y-4 pt-2 sm:pt-3">
                <button
                  className={`w-full flex justify-center items-center
                    bg-[#008ACB] text-primary rounded-md 
                    py-2.5 sm:py-3 lg:py-3.5 text-sm sm:text-base
                    transition-all duration-300
                    ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-[#0099E6]'}`}
                  type="submit"
                  disabled={isLoading}
                >
                  {isLoading ? 'Signing in...' : 'Sign in'}
                </button>

                <button
                  onClick={handleGoogleSignIn}
                  className={`w-full flex justify-center items-center gap-2
                    bg-[#000000] border-[#989898] border text-primary rounded-md 
                    py-2.5 sm:py-3 lg:py-3.5 text-sm sm:text-base
                    transition-all duration-300
                    ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-[#1A1A1A]'}`}
                  disabled={isLoading}
                >
                  <img src={googleLogo} alt="Google" className="w-5 sm:w-6" />
                  Sign in with Google
                </button>
              </div>

              {message && (
                <div className="mt-3 sm:mt-4 text-center text-xs sm:text-sm text-gray-600">
                  {message}
                </div>
              )}
            </form>

            {/* Sign Up Link */}
            <div className="mt-6 sm:mt-8 text-center">
              <p className="text-xs sm:text-sm bg-gradient-text">
                Don't have an account?{' '}
                <Link to="/register" className="text-[#008ACB] hover:text-[#4bb8eb] transition-colors">
                  Sign up
                </Link>
              </p>
            </div>
          </div>
        </div>

        {/* Logo and 3D Animation Section - Right side */}
         {/* Logo and 3D Animation Section */}
         <div className="hidden lg:flex w-[55%] relative">
          <Link to="/" className="absolute top-8 sm:top-12 right-8 sm:right-12 z-10">
            <img 
              src={velocitylogo} 
              className="h-10 sm:h-14 transition-all duration-300" 
              alt="Velocity Logo" 
            />
          </Link>
          <div className="w-full h-full flex items-center justify-center">
            <ThreeDLogo />
          </div>
        </div>
      </div>

      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent via-[12%] bottom-0" />
    </div>
  );
};

export default Login;