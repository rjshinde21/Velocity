import React, { useState } from 'react';
import launchlist from "../assets/launchlist.png";

const NewsletterSignup = () => {
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    // Add your newsletter signup logic here
    console.log('Email submitted:', email);
    
    // Simulate API call
    setTimeout(() => {
      setIsSubmitting(false);
      setEmail('');
    }, 1000);
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6">
      <div className="bg-black rounded-3xl p-8 flex flex-col sm:flex-row items-center gap-6 sm:gap-8 border border-gray-800">
        {/* Left side - Animated Character */}
        <div className="w-32 sm:w-40 flex-shrink-0">
          <div className="animate-bounce">
            <img src="" alt="" />
          </div>
        </div>

        {/* Right side - Content */}
        <div className="flex-1 space-y-4">
          <h2 className="text-white text-2xl sm:text-3xl font-bold">
            Join the Launchlist
          </h2>
          <p className="text-gray-400 text-sm sm:text-base">
            Get the updates that you need to know about the launch, plus some cool special recommendations weekly.
          </p>

          {/* Email Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Your Email"
                className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg
                  text-white placeholder-gray-500 focus:outline-none focus:border-blue-500
                  transition-colors"
                required
              />
            </div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg
                font-medium hover:bg-blue-700 focus:outline-none focus:ring-2
                focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-black
                transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Processing...' : 'Get Notified'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default NewsletterSignup;