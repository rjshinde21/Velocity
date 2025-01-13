import React, { useState, useEffect } from 'react';
import { Share2, Copy, Check } from 'lucide-react';
import Analytics from '../config/analytics';
import referralBg from '../assets/subtract.png'; // Adjust path as needed


const ShareReferral = ({ userId, authToken }) => {
    const [referralCode, setReferralCode] = useState('');
    const [referralStats, setReferralStats] = useState({
        totalReferrals: 0,
        tokensEarned: 0,
        pendingReferrals: 0
    });
    const [copied, setCopied] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);

    useEffect(() => {
        fetchReferralCode();
        fetchReferralStats();
    }, []);

    const fetchReferralCode = async () => {
        try {
            const response = await fetch('https://thinkvelocity.in/api/api/referral/generate', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_id: userId })
            });
            const data = await response.json();
            setReferralCode(data.referralCode);
        } catch (error) {
            console.error('Error fetching referral code:', error);
        }
    };

    const fetchReferralStats = async () => {
        try {
            const response = await fetch(`https://thinkvelocity.in/api/api/referral/stats/${userId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            const data = await response.json();
            setReferralStats(data.data.stats);
        } catch (error) {
            console.error('Error fetching referral stats:', error);
        }
    };

    const copyToClipboard = async () => {
        try {
            await navigator.clipboard.writeText(
                `Join Velocity AI using my referral code: ${referralCode}\nhttps://thinkvelocity.in/register?ref=${referralCode}`
            );
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (error) {
            console.error('Error copying to clipboard:', error);
        }
    };

    const shareReferral = async () => {
        if (navigator.share) {
            try {
                Analytics.track('Button Clicked',{
                    buttonName: "Share"
                });
                await navigator.share({
                    title: 'Join Velocity AI',
                    text: `Join Velocity AI using my referral code: ${referralCode}`,
                    url: `https://thinkvelocity.in/register?ref=${referralCode}`
                });
            } catch (error) {
                console.error('Error sharing:', error);
            }
        } else {
            setIsModalOpen(true);
        }
    };

    return (
      <div className="w-full font-[Inter] rounded-3xl p-6  relative overflow-hidden"
      style={{
        backgroundImage: `url(${referralBg})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center'
    }}>
            <div className="text-center mb-2 relative z-10">
                <h2 className="text-2xl text-white font-semibold">Earn More</h2>
                <h3 className="text-xl text-white mb-3">Free Credits</h3>
                <p className="text-[#999999] text-sm">
                    You Get 50 Credits • Your Friend Gets 30 Credits
                </p>
            </div>

          <button
              onClick={shareReferral}
              className="w-full bg-white hover:bg-gray-100 text-black font-medium py-3 px-6 rounded-full transition-all duration-200 flex items-center justify-center gap-2 mt-4 mb-3"
          >
              <span>Spread AI Empowerment</span>
              <Share2 className="w-4 h-4" />
          </button>

          <p className="text-[#999999] text-xs text-center">
              Refer a friend and get enough credits to optimise upto 10 complex prompts
          </p>

          {isModalOpen && (
              <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                  <div className="bg-[#1A1A1A] rounded-2xl p-6 w-full max-w-md border border-[#333333]">
                      <h3 className="text-xl text-white mb-4 text-center">Share Your Referral Code</h3>
                      
                      <div className="bg-black/30 p-4 rounded-xl flex justify-between items-center mb-6">
                          <span className="text-white font-mono">{referralCode}</span>
                          <button
                              onClick={copyToClipboard}
                              className="text-[#0084CC] hover:text-[#0095e8] transition-colors"
                          >
                              {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                          </button>
                      </div>

                      <button
                          onClick={() => setIsModalOpen(false)}
                          className="w-full bg-black/30 text-white font-medium py-3 rounded-xl hover:bg-black/40 transition-colors"
                      >
                          Close
                      </button>
                  </div>
              </div>
          )}
      </div>
  );
};

export default ShareReferral;