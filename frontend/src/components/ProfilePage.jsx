import React, { useState } from 'react';
import logo from '../assets/velocitylogo.png';
import PromptGrid from './PromptGrid';

const ProfilePage = () => {
    const [name, setName] = useState("Mukul Goyal");
    const [isEditing, setIsEditing] = useState(false);
    const [isPremium, setIsPremium] = useState(true);

    const handleClick = () => {
        setIsEditing(!isEditing);
    };

    const handleChange = (e) => {
        setName(e.target.value);
    };

    // Credits section component to avoid duplication
    const CreditsSection = () => (
        <div className="flex flex-col justify-center items-center px-10 sm:px-4 py-6 md:py-10 ">
            <div className="w-full max-w-sm sm:px-4 sm:py-5">
                <p className="text-[#ffffff]/80 font-[Inter] text-sm mb-3">Credit Balance of today</p>
                <p className="pb-3 text-[#ffffff] font-[Inter] border-b border-[#ffffff]/30">
                    <span className="text-4xl">40</span> Credits Left
                </p>
                <p className="text-[#ffffff]/80 my-3 italic font-normal font-[Inter]">Running out of daily credits?</p>
                <div className='flex sm:flex-col gap-10 sm:gap-0'>
                <button className="w-full md:w-fit flex justify-center font-[Inter] border border-[#F7AA1C] transition-all duration-200 text-[10px] px-2 py-2 sm:px-4 sm:py-3 text-primary rounded-[35px] items-center bg-[radial-gradient(circle_at_center,_rgba(247,170,28,0.2),_rgba(247,170,28,0.4))] hover:shadow-[0_0_7px_rgba(255,255,255,0.7)] my-3 sm:mb-8">
                    Top Up Credits
                </button>
            <button className="w-full max-w-sm flex justify-center text-lg px-7 py-4 sm:px-36 sm:py-5 text-[#444444] border border-[#444444] transition-all duration-200 rounded-[35px] items-center hover:shadow-[0_0_7px_rgba(255,255,255,0.7)]">
                Upgrade
            </button>
                </div>
            </div>
        </div>
    );

    return (
        <div className="flex flex-col md:flex h-screen w-screen overflow-x-hidden">
            {/* Credits section for desktop only */}
            <div className="hidden absolute items-end md:flex md:w-[485px] flex-shrink-0 bg-black h-full">
                <CreditsSection />
            </div>
            
            {/* Main content area */}
            <div className="flex-1 overflow-y-auto bg-black rounded-lg md:ml-[485px] sm:border-l border-l-[#2C2C2C]">
                <div className="flex flex-col mt-20 lg:mt-52">
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

                    {/* Credits section for mobile only - shows below profile */}
                    <div className="md:hidden w-[90%] border-t border-[#2C2C2C] mx-auto mt-6 sm:mx-0">
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