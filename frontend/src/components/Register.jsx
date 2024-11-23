import React, { useEffect, useState } from 'react';
import velocitylogo from "../assets/velocitylogo.png";
import { useNavigate, Link } from 'react-router-dom';
import ThreeDLogo from './3dLogo/ThreeDLogo';
import supabase from '../config/supabaseClient';
import googleLogo from '../assets/googleLogo.png'

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [animate, setAnimate] = useState(false);

  console.log('supabase', supabase)

  useEffect(() => {
    setAnimate(true);
  }, []);

  const navigate = useNavigate(); // Initialize navigate hook

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
    // Update the field value
    switch (field) {
      case 'name':
        setName(value);
        break;
      case 'email':
        setEmail(value);
        break;
      case 'password':
        setPassword(value);
        // Also validate confirm password when password changes
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

    // Validate and set error
    const error = validateField(field, value);
    setFieldErrors(prev => ({
      ...prev,
      [field]: error
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage('');

    try{   
      const { data, error } = await supabase.auth.signUp({
      name:name,
      email: email,
      password: password,
      confirmPassword: confirmPassword
    })
    if (error) throw error
    alert("Check your email for verification link")
  } catch(error){
    console.log(error)
  }

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
    setMessage(<span style={{ color: '2563eb' }}>Processing registration...</span>);

    try {
      const response = await fetch('http://127.0.0.1:3000/api/users/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          name,
          email,
          password,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(<span style={{ color: 'green' }}>Registration successful! Now you can login into extension using this credentials</span>);
        localStorage.setItem('registrationSuccess', 'true');
        setTimeout(() => {
          navigate('/login'); 
        }, 2000);
      } else {
        switch (response.status) {
          case 400:
            setMessage(<span style={{ color: 'red' }}>Error: {data.message || 'Invalid input data'}</span>);
            break;
          case 409:
            setMessage(<span style={{ color: 'red' }}>Email already registered. Please login instead.</span>);
            break;
          case 500:
            setMessage(<span style={{ color: 'red' }}>Server error. Please try again later.</span>);
            break;
          default:
            setMessage(<span style={{ color: 'red' }}>Error: {data.message || 'Registration failed'}</span>);
        }
      }
    } catch (error) {
      console.error('Registration error:', error);
      setMessage(<span style={{ color: 'red' }}>Network error. Please check your connection and try again.</span>);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignUp = async (e) => {
    e.preventDefault();
    try {
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: window.location.origin,
          queryParams: {
            access_type: 'offline',
            prompt: 'consent',
          },
        }
      }); 
      if(data) console.log('data', data)
  
      if (error) throw error;
  
      // Set up auth state listener to capture user data after successful sign-in
      supabase.auth.onAuthStateChange(async (event, session) => {
        console.log('Auth Event:', event);
        
        if (event === 'SIGNED_IN') {
          // Get user data
          const { data: { user }, error: userError } = await supabase.auth.getUser();
          
          if (userError) {
            console.error('Error fetching user data:', userError);
          } else {
            // Log detailed user information
            console.log('User Data:', {
              id: user.id,
              email: user.email,
              emailVerified: user.email_confirmed_at,
              lastSignIn: user.last_sign_in_at,
              createdAt: user.created_at,
              updatedAt: user.updated_at,
              userMetadata: user.user_metadata,
              appMetadata: user.app_metadata,
            });
  
            // Log Google-specific profile information
            console.log('Google Profile:', {
              name: user.user_metadata?.full_name,
              avatar: user.user_metadata?.avatar_url,
              email: user.user_metadata?.email,
            });
  
            // Log session information
            console.log('Session Info:', {
              accessToken: session?.access_token,
              tokenType: session?.token_type,
              expiresAt: session?.expires_at,
            });
  
            // Store user data in localStorage if needed
            localStorage.setItem('user', JSON.stringify({
              id: user.id,
              email: user.email,
              name: user.user_metadata?.full_name,
              avatar: user.user_metadata?.avatar_url
            }));
  
            // Navigate to home page
            navigate('/');
          }
        }
      });
  
    } catch (error) {
      console.error('Google Sign Up Error:', {
        message: error.message,
        hint: error.hint,
        status: error.status,
        details: error.details,
      });
      alert(error.message);
    }
  };

  return (
    <div className="min-h-screen bg-[#0C0C0C] sm:bg-black absolute h-full w-full flex justify-center items-center sm:flex-row flex-col z-30 sm:gap-0 gap-12">
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
            <button className='bg-[#008ACB] text-primary rounded-md w-full py-3 mt-2' content="Register" disabled={isLoading}>
              Register
            </button>
            </div>

            <div className='w-full flex justify-center'>
            <button onClick={handleGoogleSignUp} className='bg-[#000000] border-[#989898] border text-primary rounded-md w-full py-3 flex gap-2 justify-center items-center' content="Register" disabled={isLoading}>
              <img src={googleLogo} alt="Google" />Sign up with Google
            </button>
            </div>
            
          </div>

          {/* Message Area */}
          <div id="message" className="mt-4 text-center text-sm text-gray-600">
            {message}
          </div>
        </form>

        {/* Link to Login */}
        <div className="mt-4 text-center">
          <p className="text-sm bg-gradient-text">Already have an account? {' '}
          <Link to="/login" className="text-[#008ACB] hover:text-[#4bb8eb]">Log In</Link>
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

export default Register;