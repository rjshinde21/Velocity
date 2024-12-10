import React, { useState,useEffect } from 'react';
import {Link, useNavigate} from 'react-router-dom';
import velocitylogo from '../assets/velocitylogo.png';
import PromptGrid from './PromptGrid';
import BuyCredit from './buy_credit';
//import useRazorpay from "react-razorpay";

const ProfilePage = ({pricingRef}) => {
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
        console.log("fetching user profile: https://thinkvelocity.in/api/api/users/profile/"+userId)
        try {
            const response = await fetch(`https://thinkvelocity.in/api/api/users/profile/${userId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json',
                },
            });
            const data = await response.json();
            if (data && data.data && data.data.user) {
                setName(data.data.user.name); // Set name from API data
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
    const handleTopUp = async (amount) => {
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
                    amount: amount
                })
            });
    
            if (!response.ok) {
                throw new Error(`Failed to top up tokens: ${response.status}`);
            }
            
            const updatedData = await response.json();
            if (updatedData.success) {
                // Fetch updated token info to refresh the UI
                await fetchTokenDetails();
                return true; // Return true to indicate success
            } else {
                throw new Error(updatedData.message || 'Failed to top up tokens');
            }
        } catch (error) {
            console.error('Top-up error:', error);
            setError(error.message);
            throw error; // Re-throw the error to be handled by the payment flow
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
    const handlePayment = async () => {
        try {

            // Convert USD to INR
            const amountInINR = Math.round(topUpAmount * USD_TO_INR);

            // First create order on your backend
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
                key: "rzp_test_99YnTAFGwSDddP", // Replace with your key
                amount: amountInINR * 100,
                currency: "INR",
                name: "Velocity AI",
                description: `Token Top Up ($${topUpAmount} USD)`, // Show USD amount in description
                order_id: orderData.id,
                handler: async function (response) {
                    try {
                        // Verify payment on backend
                        const verifyResponse = await fetch('https://thinkvelocity.in/api/api/verify-payment', {
                            method: 'POST',
                            headers: {
                                'Authorization': `Bearer ${authToken}`,
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                userId : userId,
                                razorpay_payment_id: response.razorpay_payment_id,
                                razorpay_order_id: response.razorpay_order_id,
                                razorpay_signature: response.razorpay_signature,
                                amount: topUpAmount,
                                amountInINR: amountInINR // Send converted INR amount
                            })
                        });
                
                        const verifyData = await verifyResponse.json();
                
                        if (verifyData.success) {
                            try {
                                await handleTopUp(topUpAmount);
                                setIsTopUpModalOpen(false);
                                alert('Payment successful! Tokens have been added to your account.');
                            } catch (error) {
                                alert('Payment was successful but token update failed. Please contact support.');
                            }
                        }
                    } catch (error) {
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
        <div className="flex flex-col justify-between h-full px-6 sm:px-4 py-6 md:py-24 ">
            <div className="flex flex-col md:flex-row md:gap-16 lg:gap-32 items-center px-4 sm:mt-40">
                        <div className="text-center md:text-left mb-10 sm:mb-0">
                            {/* <button
                                className="bg-[#2C2C2C] hover:bg-gray-600 text-white text-sm px-4 py-2 rounded-lg font-[Inter] mb-4 flex gap-2 items-center mx-auto md:mx-0"
                                onClick={handleClick}
                            >
                                <svg
                                    className="w-4 h-4 mr-1"
                                    aria-hidden="true"
                                    xmlns="http://www.w3.org/2000/svg"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                >
                                    <path d={isEditing ? "M6 10h8v2H6v-2zm-2 4h12v2H4v-2z" : "M4 13V17H8L16.5 8.5L12.5 4.5L4 13ZM18.5 6L14 1.5L16.5 0L20 3.5L18.5 6Z"} />
                                </svg>
                                {isEditing ? "Save Profile" : "Edit Profile"}
                            </button> */}
                            {isEditing ? (
                                <input
                                    className="text-white w-auto font-[Inter] text-2xl md:text-3xl bg-transparent border-b border-gray-500 focus:outline-none focus:border-white text-center md:text-left"
                                    onChange={handleChange}
                                    value={name}
                                    autoFocus
                                />
                            ) : (
                                <h2 className="text-white font-[Inter] text-2xl md:text-3xl">{name}</h2>
                            )}
                            {/* <span className={`${isPremium ? 'bg-[#F7AA1C80]' : 'bg-[#D9D9D966]'} text-white text-xs px-3 py-1 rounded-lg gap-1 inline-flex items-center mt-2 italic`}>
                                {isPremium && <img className="w-3 h-3" src={logo} alt="" />}
                                {isPremium ? "Premium" : "Free Plan"} User
                            </span> */}
                        </div>
                    </div>
            <div className="w-full max-w-sm sm:px-4 sm:py-5">
                <p className="text-[#ffffff]/80 font-[Inter] text-sm mb-3">Credit Balance of today</p>
                <p className="pb-3 text-[#ffffff] font-[Inter] border-b border-[#ffffff]/30">
                    <span className="text-4xl">{(tokenInfo?.token_received || 0) - (tokenInfo?.tokens_used || 0)}</span> Credits Left
                </p>
                <p className="text-[#FFFFFF]/80 my-3 italic font-normal font-[Inter]">Running out of daily credits?</p>
                <div className='flex sm:flex-col gap-10 sm:gap-0'>
                {/* <button onClick={()=>handleUpgrade(pricingRef)}
     
    className="w-full max-w-sm flex justify-center text-lg px-7 py-4 sm:px-36 sm:py-5 text-[#BEBEBE] border border-[#F7AA1C] shadow-[0_0_9px_rgba(247,170,28,0.3)] transition-all duration-200 rounded-[35px] items-center hover:shadow-[0_0_12px_rgba(247,170,28,0.7)]"
>
    Upgrade
</button> */}
            <button 
                onClick={() => setIsTopUpModalOpen(true)}
                className="w-full max-w-sm flex justify-center text-lg px-7 py-4 sm:px-36 sm:py-5 text-[#BEBEBE] border border-[#F7AA1C] shadow-[0_0_9px_rgba(247,170,28,0.3)] transition-all duration-200 rounded-[35px] items-center hover:shadow-[0_0_12px_rgba(247,170,28,0.7)]"
            >
                Top Up
            </button>


<button 
    onClick={handleLogout} 
    className="w-fit flex justify-center text-sm px-6 py-2 sm:px-6 sm:py-2 mt-4 text-[#ffffff]/30 border border-[#ffffff]/30 transition-all duration-200 rounded-[35px] items-center hover:shadow-[0_0_7px_rgba(255,255,255,0.7)]"
>
    Logout
</button>

                </div>
            </div>
        </div>
    );
    // const TopUpModal = () => (
    //     <div className={`fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 ${isTopUpModalOpen ? '' : 'hidden'}`}>
    //         <div className="bg-[#1C1C1C] rounded-lg p-6 w-96">
    //             <h2 className="text-white text-xl mb-4">Top Up Tokens</h2>
    //             <div className="mb-4">
    //                 <label className="text-white text-sm mb-2 block">Select Amount (INR)</label>
    //                 <select 
    //                     value={topUpAmount}
    //                     onChange={(e) => setTopUpAmount(Number(e.target.value))}
    //                     className="w-full bg-[#2C2C2C] text-white rounded px-3 py-2"
    //                 >
    //                     <option value="100">100 Tokens - ₹100</option>
    //                     <option value="500">500 Tokens - ₹500</option>
    //                     <option value="1000">1000 Tokens - ₹1000</option>
    //                     <option value="2000">2000 Tokens - ₹2000</option>
    //                 </select>
    //             </div>
    //             <div className="flex justify-end gap-3">
    //                 <button 
    //                     onClick={() => setIsTopUpModalOpen(false)}
    //                     className="px-4 py-2 text-white border border-gray-600 rounded hover:bg-gray-700"
    //                 >
    //                     Cancel
    //                 </button>
    //                 <button 
    //                     onClick={handlePayment}
    //                     className="px-4 py-2 bg-[#F7AA1C] text-white rounded hover:bg-[#d89116]"
    //                 >
    //                     Proceed to Pay
    //                 </button>
    //             </div>
    //         </div>
    //     </div>
    // );

      
      
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
          <div className="hidden absolute items-end md:flex md:w-[485px] flex-shrink-0 bg-black h-full justify-center">
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