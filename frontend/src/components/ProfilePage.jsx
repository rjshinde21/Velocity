import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Coins } from 'lucide-react';
import logo from '../assets/velocitylogo.png';
import PromptGrid from './PromptGrid';

const ProfilePage = () => {
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

    useEffect(() => {
        const checkAuthAndFetchTokens = async () => {
            if (!authToken || !userId) {
                setError('Authentication required');
                navigate('/login');
                return;
            }
            await fetchTokenDetails();
            await fetchUserProfile(); // Fetch the user's name here
        };

        checkAuthAndFetchTokens();
    }, [navigate, isUpdating]);

    const fetchUserProfile = async () => {
        try {
            const response = await fetch(`http://127.0.0.1:3000/api/users/profile/${userId}`, {
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

            const response = await fetch(`http://127.0.0.1:3000/api/token-types/${userId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                credentials: 'include'
            });

            if (response.status === 401) {
                localStorage.clear();
                navigate('/login');
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

            if (err.message.includes('Session expired') || err.message.includes('Invalid data format')) {
                navigate('/login');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleTopUp = async () => {
        if (!authToken || !userId) {
            setError('Authentication required.');
            return;
        }

        try {
            setIsUpdating(true);
            setError(null);

            const response = await fetch(`http://127.0.0.1:3000/api/token-types/${userId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    token_received: tokenInfo.token_received,
                    user_id: userId
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to update tokens: ${response.status}`);
            }

            const updatedData = await response.json();

            if (updatedData && updatedData.data) {
                setTokenInfo(updatedData.data);
                alert('Successfully topped up credits!');
            }

        } catch (error) {
            console.error('Top-up error:', error);
            setError(error.message);
            alert('Failed to top up tokens. Please try again.');
        } finally {
            setIsUpdating(false);
        }
    };

    const handleClick = () => {
        setIsEditing(!isEditing);
    };

    const handleChange = (e) => {
        setName(e.target.value);
    };

    // Credits section component with TokenInfo integration
    const CreditsSection = () => (
        <div className="flex flex-col justify-center items-center px-10 sm:px-4 py-6 md:py-10">
            {isLoading ? (
                <div className="flex items-center justify-center p-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                </div>
            ) : error ? (
                <div className="text-red-500 text-center">
                    <p>{error}</p>
                    <button
                        onClick={fetchTokenDetails}
                        className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                    >
                        Try Again
                    </button>
                </div>
            ) : (
                <div className="w-full max-w-sm sm:px-4 sm:py-5">
                    <div className="flex items-center mb-3">
                        <Coins className="w-6 h-6 text-yellow-500 mr-2" />
                        <p className="text-[#ffffff]/80 font-[Inter] text-sm">Credit Balance of today</p>
                    </div>
                    <p className="pb-3 text-[#ffffff] font-[Inter] border-b border-[#ffffff]/30">
                        <span className="text-4xl">{tokenInfo?.token_received || 0}</span> Credits Left
                    </p>
                    <p className="text-[#ffffff]/80 my-3 italic font-normal font-[Inter]">Running out of daily credits?</p>
                    <div className='flex sm:flex-col gap-10 sm:gap-0'>
                        <button 
                            className="w-full md:w-fit flex justify-center font-[Inter] border border-[#F7AA1C] transition-all duration-200 text-[10px] px-2 py-2 sm:px-4 sm:py-3 text-primary rounded-[35px] items-center bg-[radial-gradient(circle_at_center,_rgba(247,170,28,0.2),_rgba(247,170,28,0.4))] hover:shadow-[0_0_7px_rgba(255,255,255,0.7)] my-3 sm:mb-8"
                            onClick={handleTopUp}
                            disabled={isUpdating}
                        >
                            {isUpdating ? 'Processing...' : 'Top Up Credits'}
                        </button>
                        <button className="w-full max-w-sm flex justify-center text-lg px-7 py-4 sm:px-36 sm:py-5 text-[#444444] border border-[#444444] transition-all duration-200 rounded-[35px] items-center hover:shadow-[0_0_7px_rgba(255,255,255,0.7)]">
                            Upgrade
                        </button>
                    </div>
                </div>
            )}
        </div>
    );

    return (
        <div className="flex flex-col md:flex h-screen w-screen overflow-x-hidden">
            {/* Rest of your JSX remains the same */}
            <div className="hidden absolute items-end md:flex md:w-[485px] flex-shrink-0 bg-black h-full">
                <CreditsSection />
            </div>
            
            <div className="flex-1 overflow-y-auto bg-black rounded-lg md:ml-[485px] sm:border-l border-l-[#2C2C2C]">
                <div className="flex flex-col mt-6 md:mt-12 lg:mt-52">
                    {/* Profile Section */}
                    <div className="flex flex-col md:flex-row md:gap-16 lg:gap-32 items-center p-4 md:p-8">
                        <img
                            src=""
                            alt="Profile"
                            className="w-20 h-20 md:w-24 md:h-24 lg:w-52 lg:h-52 border rounded-full overflow-hidden mb-4 md:mb-0"
                        />
                        <div className="text-center md:text-left">
                            <button
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
                            </button>

                            {isEditing ? (
                                <input
                                    className="text-white font-[Inter] text-2xl md:text-3xl bg-transparent border-b border-gray-500 focus:outline-none focus:border-white text-center md:text-left"
                                    onChange={handleChange}
                                    value={name}
                                    autoFocus
                                />
                            ) : (
                                <h2 className="text-white font-[Inter] text-2xl md:text-3xl">{name}</h2>
                            )}
                            <span className={`${isPremium ? 'bg-[#F7AA1C80]' : 'bg-[#D9D9D966]'} text-white text-xs px-3 py-1 rounded-lg gap-1 inline-flex items-center mt-2 italic`}>
                                {isPremium && <img className="w-3 h-3" src={logo} alt="" />}
                                {isPremium ? "Premium" : "Free Plan"} User
                            </span>
                        </div>
                    </div>

                    {/* Credits section for mobile only */}
                    <div className="md:hidden w-[90%] border-t border-[#2C2C2C] mx-auto mt-6 sm:mx-0">
                        <CreditsSection />
                    </div>

                    <PromptGrid />
                </div>
            </div>
        </div>
    );
};

export default ProfilePage;