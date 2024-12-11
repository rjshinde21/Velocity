import React, { useState } from 'react';
import launchlist from "../assets/launchlist.png";
import { X } from 'lucide-react';

const LaunchlistModal = ({ isOpen, onClose }) => {
    const [email, setEmail] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        console.log('Email submitted:', email);
        setTimeout(() => {
            setIsSubmitting(false);
            setEmail('');
            onClose();
        }, 1000);
    };

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 sm:p-6 md:p-8">
            <div className="relative w-full max-w-[95%] sm:max-w-2xl md:max-w-3xl lg:max-w-4xl mx-auto">
                <div className="bg-black rounded-xl sm:rounded-2xl md:rounded-3xl p-6 sm:p-8 md:p-10 
        flex flex-col sm:flex-row items-center gap-6 sm:gap-8 md:gap-10 
        border border-gray-800">
                    {/* Close button */}
                    <button
                        onClick={onClose}
                        className="absolute top-3 right-3 sm:top-5 sm:right-5 
            text-gray-400 hover:text-white transition-colors 
            p-1.5 sm:p-2 hover:bg-gray-800 rounded-full"
                    >
                        <X className="w-5 h-5 sm:w-6 sm:h-6 md:w-7 md:h-7" />
                    </button>

                    {/* Left side - Animated Character */}
                    <div className="w-40 sm:w-56 md:w-72 lg:w-80 flex-shrink-0">
                        <div className="animate-bounce">
                            <img
                                src={launchlist}
                                alt="Launchlist"
                                className="w-full h-full object-contain"
                                draggable="false"
                            />
                        </div>
                    </div>

                    {/* Right side - Content */}
                    <div className="flex-1 space-y-4 sm:space-y-5">
                        <h2 className="text-white text-2xl sm:text-3xl md:text-4xl font-bold text-center sm:text-left">
                            Join the Launchlist
                        </h2>
                        <p className="text-gray-400 text-sm sm:text-base md:text-lg text-center sm:text-left">
                            Get the updates that you need to know about the launch, plus some cool special recommendations weekly.
                        </p>

                        {/* Email Form */}
                        <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-5">
                            <div className="relative">
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="Your Email"
                                    className="w-full px-4 sm:px-5 py-3 sm:py-4 
                  bg-gray-900 border border-gray-700 
                  rounded-lg text-base sm:text-lg
                  text-white placeholder-gray-500 
                  focus:outline-none focus:border-blue-500 
                  transition-colors"
                                    required
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="w-full glowing-button px-5 py-3 sm:px-7 sm:py-4 
                text-base sm:text-lg flex justify-center items-center 
                gap-2 transition-all duration-200"
                            >
                                {isSubmitting ? 'Processing...' : 'Get Notified'}
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>

    );
};

export default LaunchlistModal;