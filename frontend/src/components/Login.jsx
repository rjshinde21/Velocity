import React, { useState, useEffect  } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { GoogleAuthProvider, signInWithPopup } from 'firebase/auth';
import { auth } from '../config/firebaseConfig';
import velocitylogo from "../assets/velocitylogo.png";
import googleLogo from '../assets/googleLogo.png';
import ThreeDLogo from './3dLogo/ThreeDLogo';
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
      localStorage.setItem('userName', authData.user.username);
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
    localStorage.setItem('userName', userData.username);
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
    <div className="min-h-screen bg-[#0C0C0C] sm:bg-black fixed h-full w-full flex justify-center items-center z-30 flex-col sm:flex-row sm:gap-0 gap-12">
      <div className="bg-[#0C0C0C] sm:bg-black/60 order-2 sm:order-1 rounded-lg shadow-sm py-6 px-6 sm:px-36 sm:w-1/2 w-full" style={{zIndex: 2}}>
        <h2 className="text-left text-3xl sm:text-[42px] font-normal text-primary mb-4">Welcome back!</h2>
        <h2 className="text-left text-[16px] font-normal text-[#808080] mb-10">Please enter your details.</h2>
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

            <div className='w-full flex justify-center'>
            <button onClick={handleGoogleSignIn} className='bg-[#000000] border-[#989898] border text-primary rounded-md w-full py-3 flex gap-2 justify-center items-center' content="Register" disabled={isLoading}>
              <img src={googleLogo} alt="Google" />Sign in with Google
            </button>
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
      <div className="flex justify-center order-1 sm:order-2 items-center w-1/2 h-[20vh] sm:h-screen bg-[#0C0C0C]">
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
      {/* <div
        className={`w-24 h-24 sm:w-64 sm:h-64 bg-[#008ACB] rounded-full transform transition-opacity duration-700 ${
          animate ? "animate-slideUp opacity-100" : "opacity-0"
        }`}
        style={{
          animation: animate ? "circleSlideUp 2s ease-out" : "none",
        }}
      ></div>

      <div className="absolute top-1/2 sm:left-[-60px] w-40 h-32 left-[-35px] sm:w-96 sm:h-96 backdrop-blur-md bg-[#0C0C0C]/40"></div> */}
      <ThreeDLogo />
    </div>
    </div>
    </div>
  );
};

export default Login;