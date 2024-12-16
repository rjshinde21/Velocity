import React, { useState, useEffect } from 'react';
import { Share2, Copy, Check } from 'lucide-react';
import Analytics from '../config/analytics';

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
        <div className="w-full font-[Inter] max-w-sm mx-auto bg-[#1A1A1A] rounded-2xl p-4 sm:p-6 mt-0 mb-0 border border-[#333333]/30 mt-4 mb-4">
            <h2 className="text-white/90 text-base sm:text-lg text-center mb-4 sm:mb-6">
                For Each Referral
            </h2>

            <div className="flex flex-row justify-between gap-4 sm:gap-2 mb-6 sm:mb-6">
    <div className="text-center bg-black/30 p-3 sm:p-4 rounded-xl backdrop-blur-sm flex flex-col justify-center items-center w-full sm:min-w-[140px] min-h-[100px] sm:min-h-[120px]">
        <p className="text-gray-400 text-xs sm:text-sm mb-1 sm:mb-2">Your Friend Gets</p>
        {/* {referralStats.pendingReferrals} */}
        <p className="text-white text-3xl sm:text-4xl font-semibold">30</p>
    </div>

    <div className="text-center bg-black/30 p-3 sm:p-4 rounded-xl backdrop-blur-sm flex flex-col justify-center items-center w-full sm:min-w-[140px] min-h-[100px] sm:min-h-[120px]">
        <p className="text-gray-400 text-xs sm:text-sm mb-1 sm:mb-2">You Get</p>
        {/* {referralStats.tokensEarned} */}
        <p className="text-white text-3xl sm:text-4xl font-semibold">50</p>
    </div>
</div>

            <div className='flex justify-center items-center'>
                {/* <p className="text-[#F7AA1C] text-2xl">{referralStats.totalReferrals}</p> */}
                <p className="text-[#ffffff]/60 text-sm">You've Earned {referralStats.tokensEarned || 0} tokens till now</p>
            </div>

            <div className="flex items-center justify-center pt-6">
                <button
                    onClick={shareReferral}
                    className="bg-[#0084CC] hover:bg-[#0095e8] text-white font-medium py-2.5 sm:py-3 px-4 sm:px-6 rounded-full transition-all duration-200 flex items-center justify-center gap-1 text-sm sm:text-base"
                >
                    <Share2 className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                    Share Now
                </button>
            </div>

            {/* Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-[#1A1A1A] rounded-xl p-4 sm:p-6 w-full max-w-[90%] sm:max-w-md border border-[#333333]/30">
                        <h2 className="text-white text-lg sm:text-xl mb-4">Share Your Referral Code</h2>
                        <div className="bg-[#2C2C2C] p-3 sm:p-4 rounded-lg flex justify-between items-center mb-4 sm:mb-6">
                            <span className="text-white font-mono text-sm sm:text-base">{referralCode}</span>
                            <button
                                onClick={copyToClipboard}
                                className="text-[#0084CC] hover:text-[#0095e8] transition-colors"
                            >
                                {copied ? <Check className="w-4 h-4 sm:w-5 sm:h-5" /> : <Copy className="w-4 h-4 sm:w-5 sm:h-5" />}
                            </button>
                        </div>
                        <button
                            onClick={() => setIsModalOpen(false)}
                            className="w-full bg-[#2C2C2C] text-white font-medium py-2.5 sm:py-3 rounded-lg hover:bg-[#3C3C3C] transition-colors text-sm sm:text-base"
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