import React, { useState } from 'react';
import logo from '../assets/velocitylogo.png';
import PromptGrid from './PromptGrid';

const ProfilePage = () => {
    const [name, setName] = useState("Mukul Goyal");
    const [isEditing, setIsEditing] = useState(false);

    const handleClick = () => {
        setIsEditing(!isEditing);
    };

    const handleChange = (e) => {
        setName(e.target.value);
    };

    return (
        <div className="md:flex h-[100vh] w-[100vw]">
            <div className="flex-column justify-center sm:justify-normal sm:w-[485px] border-r border-r-[#2C2C2C] flex space-y-4 text-sm text-gray-500 dark:text-gray-400 md:me-4 mb-4 md:mb-0 sm:px-6 sm:py-5 items-center">
                <div className="px-4 py-10">
                    <div className="sm:px-4 sm:py-5">
                        <p className="text-[#ffffff]/80 font-[Inter] text-sm mb-3">Credit Balance of today</p>
                        <p className="pb-3 text-[#ffffff] font-[Inter] border-b border-[#ffffff]/30">
                            <span className="text-4xl">40</span> Credits Left
                        </p>
                        <p className="text-[#ffffff]/80 my-3 italic font-normal font-[Inter]">Running out of daily credits?</p>
                        <button className="flex font-[Inter] border border-[#F7AA1C] transition-all duration-200 text-[10px] px-2 py-2 sm:px-4 sm:py-3 text-primary rounded-[35px] items-center bg-[radial-gradient(circle_at_center,_rgba(247,170,28,0.2),_rgba(247,170,28,0.4))] hover:shadow-[0_0_7px_rgba(255,255,255,0.7)] mb-4 sm:mb-8">
                            Top Up Credits
                        </button>
                    </div>
                    <button className="flex justify-center text-lg px-7 py-3 sm:px-36 sm:py-5 text-[#444444] border border-[#444444] transition-all duration-200 rounded-[35px] items-center hover:shadow-[0_0_7px_rgba(255,255,255,0.7)]">
                        Upgrade
                    </button>
                </div>
            </div>
            <div className="flex items-center p-4 bg-black rounded-lg">
                <div className="flex flex-col mt-12 sm:mt-28">
                    <div className="flex gap-10 sm:gap-32 justify-center sm:justify-normal items-center">
                        <img
                            src=""
                            alt="Profile"
                            className="object-cover w-24 h-24 sm:w-52 sm:h-52 border rounded-full overflow-hidden"
                        />
                        <div>
                            <button
                                className="bg-[#2C2C2C] hover:bg-gray-600 text-white text-sm px-4 py-2 rounded-lg font-[Inter] mb-4 flex gap-2 items-center"
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
                                    className="text-white font-[Inter] text-3xl bg-transparent border-b border-gray-500 focus:outline-none focus:border-white"
                                    onChange={handleChange}
                                    value={name}
                                    autoFocus
                                />
                            ) : (
                                <h2 className="text-white font-[Inter] text-3xl">{name}</h2>
                            )}
                            <span className="bg-[#F7AA1C80] text-white text-xs px-3 py-1 rounded-lg gap-1 inline-flex items-center mt-2 italic">
                                <img className="w-3 h-3" src={logo} alt="" />
                                Premium User
                            </span>
                        </div>
                    </div>
                    <PromptGrid />
                </div>
            </div>
        </div>
    );
};

export default ProfilePage;
