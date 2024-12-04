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
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('sharedUser');
    
    if (storedToken && storedUser) {
      setIsLoggedIn(true);
      navigate('/profile');
    }
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
      const response = await fetch('http://localhost:3000/api/users/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();
      console.log("login api data:"+data);
      if (response.ok) {
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
      const provider = new GoogleAuthProvider();
      provider.addScope('email');
      provider.addScope('profile');
      
      const result = await signInWithPopup(auth, provider);
      const user = result.user;
      
      // Try to login with Google credentials
      const response = await fetch('http://localhost:3000/api/users/login', {
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
        setMessage(<span style={{ color: 'green' }}>Login successful! Redirecting...</span>);
        setTimeout(() => {
          navigate('/profile');
        }, 1000);
      } else if (response.status === 404) {
        setMessage(
          <span style={{ color: 'red' }}>
            Account does not exist. Please{' '}
            <Link to="/register" className="text-[#008ACB] hover:text-[#4bb8eb]">
              register
            </Link>
            {' '}first.
          </span>
        );
      } else {
        throw new Error(data.message || 'Login failed');
      }
      
    } catch (error) {
      console.error('Google Sign In Error:', error);
      setMessage(<span style={{ color: 'red' }}>Failed to connect with Google. Please try again.</span>);
    } finally {
      setIsLoading(false);
    }
  };
  




  const handleSuccessfulLogin = (userData, token) => {
    // setAuthData(userData, {
    //   token: token,
    //   userId: userData.id
    // });
    console.log("successfull login");
    localStorage.setItem('token', token);
    localStorage.setItem('userId', userData.id);
    localStorage.setItem('userEmail', userData.email);
    localStorage.setItem('userName', userData.username);

    setIsLoggedIn(true);
    setMessage(<span style={{ color: 'green' }}>Login successful! Redirecting...</span>);
    setTimeout(() => navigate('/profile'), 1000);
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