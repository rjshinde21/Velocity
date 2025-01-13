import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import velocitylogo from '../assets/velocitylogo.png';
import PromptGrid from './PromptGrid';
import BuyCredit from './buy_credit';
//import useRazorpay from "react-razorpay";
import ShareReferral from './ShareReferral';
import Analytics from '../config/analytics';
const ProfilePage = ({ pricingRef }) => {
    const [name, setName] = useState("");
    const [isEditing, setIsEditing] = useState(false);
    const [isPremium, setIsPremium] = useState(false);
    const [tokenInfo, setTokenInfo] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isUpdating, setIsUpdating] = useState(false);
    const [error, setError] = useState(null);
    const navigate = useNavigate();
    const userId = localStorage.getItem('userId');
    const authToken = localStorage.getItem('token');
    const [isTopUpModalOpen, setIsTopUpModalOpen] = useState(false);
    const [topUpAmount, setTopUpAmount] = useState(100); // Default amount
    const [isInitialized, setIsInitialized] = useState(false);  // New state

    const authMethod = localStorage.getItem('authMethod');
    console.log("user id retrieved:" + authToken);
    useEffect(() => {
        let mounted = true;
        const authMethod = localStorage.getItem('authMethod');
        const initializeProfile = async () => {
            if (!authToken || !userId) {
                if (mounted) {
                    setError('Authentication required');
                    navigate('/login');
                }
                return;
            }

            try {

                // Only verify token for Google auth
                if (authMethod === 'google') {
                    const verifyResponse = await fetch('https://thinkvelocity.in/api/api/users/verify-token', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${authToken}`,
                            'Content-Type': 'application/json'
                        }
                    });

                    if (!verifyResponse.ok && mounted) {
                        throw new Error('Token verification failed');
                    }
                }

                if (mounted) {
                    setIsInitialized(true);
                }
            } catch (error) {
                console.error('Initialization error:', error);
                if (mounted && authMethod === 'google') {
                    navigate('/login');
                }
            }
        };

        initializeProfile();

        return () => {
            mounted = false;
        };
    }, [authToken, userId, authMethod, navigate]);
    useEffect(() => {
        let mounted = true;
        const authMethod = localStorage.getItem('authMethod');
        const fetchData = async () => {
            if (!isInitialized) return;

            setIsLoading(true);
            try {
                // Fetch token details and user profile in parallel
                const [tokenResponse, profileResponse] = await Promise.all([
                    fetch(`https://thinkvelocity.in/api/api/token-types/${userId}`, {
                        headers: {
                            'Authorization': `Bearer ${authToken}`,
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        }
                    }),
                    fetch(`https://thinkvelocity.in/api/api/users/profile/${userId}`, {
                        headers: {
                            'Authorization': `Bearer ${authToken}`,
                            'Content-Type': 'application/json',
                        }
                    })
                ]);

                if (!mounted) return;

                if (tokenResponse.status === 401 || profileResponse.status === 401) {
                    if (authMethod === 'google') {
                        localStorage.clear();
                        navigate('/login');
                    }
                    throw new Error('Session expired. Please login again.');
                }

                const tokenData = await tokenResponse.json();
                const profileData = await profileResponse.json();

                if (mounted) {
                    if (tokenData.data) {
                        setTokenInfo(tokenData.data);
                    }
                    if (profileData.data?.user?.name) {
                        setName(profileData.data.user.name);
                    }
                }
            } catch (error) {
                console.error('Data fetch error:', error);
                if (mounted) {
                    setError(error.message);
                }
            } finally {
                if (mounted) {
                    setIsLoading(false);
                }
            }
        };

        fetchData();

        return () => {
            mounted = false;
        };
    }, [isInitialized, userId, authToken, authMethod, navigate, isUpdating]);


    const fetchUserProfile = async () => {
        console.log("fetching user profile: https://thinkvelocity.in/api/api/users/profile/" + userId)
        try {
            const response = await fetch(`https://thinkvelocity.in/api/api/users/profile/${userId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json',
                },
            });
            const data = await response.json();
            if (data && data.data && data.data.user) {
                setName(data.data.user.name);
            } else {
                throw new Error('Unable to fetch user profile.');
            }
        } catch (error) {
            console.error("Error fetching profile:", error);
            setError(error.message);
        }
    };
    const fetchTokenDetails = async () => {
        try {
            setIsLoading(true);
            setError(null);
            const response = await fetch(`https://thinkvelocity.in/api/api/token-types/${userId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
            });

            if (response.status === 401) {
                const authMethod = localStorage.getItem('authMethod');
                if (authMethod === 'google') {
                    // Only clear storage and redirect for Google auth
                    localStorage.clear();
                    navigate('/login');
                }
                throw new Error('Session expired. Please login again.');
            }

            if (!response.ok) {
                throw new Error(`Error: ${response.status}`);
            }

            const responseData = await response.json();
            if (responseData.data) {
                setTokenInfo(responseData.data);
            } else {
                throw new Error('Invalid data format received');
            }
        } catch (err) {
            console.error('Token fetch error:', err);
            setError(err.message);

            // Only redirect for specific errors or Google auth
            const authMethod = localStorage.getItem('authMethod');
            if (authMethod === 'google' ||
                err.message.includes('Session expired') ||
                err.message.includes('Invalid data format')) {
                navigate('/login');
            }
        } finally {
            setIsLoading(false);
        }
    };
    const handleTopUp = async ({ amount, credits }) => {
        console.log("top up:" + credits);
        if (!authToken || !userId) {
            setError('Authentication required.');
            return;
        }
        try {
            setIsUpdating(true);
            setError(null);
            const response = await fetch(`https://thinkvelocity.in/api/api/token-types/${userId}/topup`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    amount: credits // Use credits instead of amount
                })
            });
            if (!response.ok) {
                throw new Error(`Failed to top up tokens: ${response.status}`);
            }

            const updatedData = await response.json();
            if (updatedData.success) {
                Analytics.track('TopUp Successfull',
                    {
                        amount:amount,
                        credits:credits
                    });
                await fetchTokenDetails();
                return true;
            } else {
                Analytics.track('TopUp Failed',
                    {
                        amount:amount,
                        credits:credits,
                        error:updatedData.message
                    });
                throw new Error(updatedData.message || 'Failed to top up tokens');
            }
        } catch (error) {
            console.error('Top-up error:', error);
            setError(error.message);
            throw error;
        } finally {
            setIsUpdating(false);
        }
    };


    const handleUpgrade = () => {
        if (pricingRef && pricingRef.current) {
            pricingRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    };

    const handleClick = () => {
        setIsEditing(!isEditing);
    };
    const handleChange = (e) => {
        setName(e.target.value);
    };

    const handleLogout = () => {
        console.log('Logout button clicked');
        try {
            const authMethod = localStorage.getItem('authMethod');

            // Clear all storage
            localStorage.clear();
            sessionStorage.clear();

            // Clear cookies
            document.cookie.split(";").forEach((cookie) => {
                const name = cookie.split("=")[0].trim();
                document.cookie = `${name}=;expires=${new Date(0).toUTCString()};path=/;`;
            });

            console.log('All data cleared. Redirecting...');
            Analytics.track('Button Clicked', {
                buttonName: 'Logout'
              });
            // For Google auth, ensure Firebase signout
            if (authMethod === 'google' && auth) {
                auth.signOut().catch(console.error);
            }

            window.location.href = '/login';
        } catch (error) {
            console.error('Logout failed:', error);
            alert('Logout failed. Please try again.');
        }
    };


    // USD to INR conversion rate (you might want to fetch this from an API)
    const USD_TO_INR = 83.27;
    const handlePayment = async ({ amount, credits }) => {
        Analytics.track('Payment Initiated',
            {
                amount:amount,
                credits:credits
            }
        )
        try {
            const amountInINR = amount;
            console.log("amout in INR:" + amountInINR + "credits:" + credits);
            const orderResponse = await fetch('https://thinkvelocity.in/api/api/create-order', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    amount: amountInINR * 100, // Razorpay expects amount in paise
                })
            });

            const orderData = await orderResponse.json();

            const options = {
                key: "rzp_test_99YnTAFGwSDddP",
                amount: amountInINR * 100,
                currency: "INR",
                name: "Velocity AI",
                description: `Token Top Up (${credits} Credits)`, // Updated to show credits
                order_id: orderData.id,
                handler: async function (response) {
                    try {
                        const verifyResponse = await fetch('https://thinkvelocity.in/api/api/verify-payment', {
                            method: 'POST',
                            headers: {
                                'Authorization': `Bearer ${authToken}`,
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                userId: userId,
                                razorpay_payment_id: response.razorpay_payment_id,
                                razorpay_order_id: response.razorpay_order_id,
                                razorpay_signature: response.razorpay_signature,
                                amount: amount,
                                amountInINR: amountInINR,
                                credits: credits // Added credits to verification payload
                            })
                        });

                        const verifyData = await verifyResponse.json();

                        if (verifyData.success) {
                            try {
                                await handleTopUp({ amount, credits });
                                Analytics.track('Payment Completed',
                                    {
                                        amount:amount,
                                        credits:credits
                                    });
                                setIsTopUpModalOpen(false);
                                alert('Payment successful! Tokens have been added to your account.');
                            } catch (error) {
                                alert('Payment was successful but token update failed. Please contact support.');
                            }
                        }
                    } catch (error) {
                        Analytics.track('Payment Failed',
                            {
                                amount:amount,
                                credits:credits,
                                error:error
                            });
                        console.error('Payment verification failed:', error);
                        alert('Payment verification failed. Please contact support.');
                    }
                }
            };

            const paymentObject = new window.Razorpay(options);
            paymentObject.open();

        } catch (error) {
            console.error('Payment initiation failed:', error);
            alert('Unable to initiate payment. Please try again.');
        }
    };


    // Credits section component to avoid duplication
    const CreditsSection = () => (
        <div className="flex flex-col h-full px-4 sm:px-6 lg:px-8 py-6 lg:py-24">
  {/* Profile Section */}
  <div className="flex flex-col items-center lg:items-start 
    px-2 sm:px-4 
    mt-4 sm:mt-8 lg:mt-20"
  >
    <div className="text-center lg:text-left mb-8 w-full lg:w-auto">
      {isEditing ? (
        <input
          className="text-white w-full lg:w-auto 
            font-[Inter] text-xl sm:text-2xl lg:text-3xl 
            bg-transparent border-b border-gray-500 
            focus:outline-none focus:border-white 
            text-center lg:text-left px-2"
          onChange={handleChange}
          value={name}
          autoFocus
        />
      ) : (
        <h2 className="text-white font-[Inter] text-xl sm:text-2xl lg:text-3xl">
          {name}
        </h2>
      )}
    </div>
  </div>

  {/* Credits Section */}
  <div className="w-full max-w-md mx-auto px-4 mr-8">
    {/* Credit Balance Title */}
    <p className="text-[#ffffff]/80 font-[Inter] 
      text-xs sm:text-sm lg:text-base 
      mb-2 sm:mb-4"
    >
      Credit Balance of today
    </p>
    
    {/* Balance Display */}
    <p className="pb-2 sm:pb-4 
      text-[#ffffff] font-[Inter] 
      border-b border-[#ffffff]/30"
    >
      <span className="text-2xl sm:text-3xl lg:text-4xl">
        {(tokenInfo?.token_received || 0) - (tokenInfo?.tokens_used || 0)}
      </span>
      <span className="text-sm sm:text-base lg:text-lg ml-2 sm:ml-3">
        Credits Left
      </span>
    </p>

    {/* Credits Message */}
    <p className="text-[#FFFFFF]/80 
      my-2 sm:my-4 
      italic font-normal font-[Inter] text-sm"
    >
      Running out of daily credits?
    </p>

    {/* Buttons Section */}
    <div className="flex flex-col gap-4 mt-4 sm:mt-6">
      {/* Top Up Button */}
      <button
        onClick={() => {
        Analytics.track('Button Clicked', {
            buttonName: 'TopUp'
          });
          setIsTopUpModalOpen(true);
      }}
        className="w-full flex justify-center items-center 
          text-base sm:text-lg 
          px-4 sm:px-8 py-3 sm:py-4 
          text-[#BEBEBE] border border-[#F7AA1C] 
          shadow-[0_0_9px_rgba(247,170,28,0.3)] 
          transition-all duration-200 rounded-[35px] 
          hover:shadow-[0_0_12px_rgba(247,170,28,0.7)]"
      >
        Top Up
      </button>

      {/* Share Referral Component */}
      <ShareReferral userId={userId} authToken={authToken} />

      {/* Logout Button */}
      <button
        onClick={handleLogout}
        className="w-full flex justify-center items-center 
          text-xs sm:text-sm 
          px-4 sm:px-6 py-2 sm:py-3
          text-[#ffffff]/30 border border-[#ffffff]/30 
          transition-all duration-200 rounded-[35px] 
          hover:shadow-[0_0_7px_rgba(255,255,255,0.7)]"
      >
        Logout
      </button>
    </div>
  </div>
</div>
    );

    return (
        <div className="flex flex-col md:flex h-screen w-screen overflow-x-hidden">
            {/* Buy Credit Modal */}
            <BuyCredit
                isOpen={isTopUpModalOpen}
                onClose={() => setIsTopUpModalOpen(false)}
                setTopUpAmount={setTopUpAmount}
                handlePayment={handlePayment}
            />

            {/* Credits section for desktop only */}
            <div className="hidden absolute items-end md:flex md:w-[485px] flex-shrink-0 bg-[#008ACB] h-full justify-center">
                <CreditsSection />
            </div>

            {/* Main content area */}
            <div className="flex-1 overflow-y-auto bg-black rounded-lg md:ml-[485px] sm:border-l border-l-[#2C2C2C]">
                <div className="flex flex-col mt-0 lg:mt-0">
                    {/* Profile Section */}
                    <Link
                        to="/"
                        className={
                            'flex items-center space-x-3 sm:w-auto w-auto absolute top-5 sm:top-12 left-4 sm:left-12 px-4 '
                        }
                    >
                        <img src={velocitylogo} className="h-10 sm:h-14" alt="Velocity Logo" />
                    </Link>

                    {/* Credits section for mobile only */}
                    <div className="md:hidden w-[90%] sm:border-t border-[#2C2C2C] mx-auto mt-6 sm:mx-0">
                        <CreditsSection />
                    </div>

                    {/* PromptGrid will be scrollable if content grows */}
                    <PromptGrid />
                </div>
            </div>
        </div>
    );
};

export default ProfilePage; 