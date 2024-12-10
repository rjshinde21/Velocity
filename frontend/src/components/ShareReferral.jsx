import React, { useState, useEffect } from 'react';
import { Share2, Copy, Check } from 'lucide-react';

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
    console.log("user id inside share referral:"+userId);
    const fetchReferralCode = async () => {
        try {
            const response = await fetch('https://thinkvelocity.in/api/api/referral/generate', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_id : userId })
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
            console.log("referal stats:"+data.data.stats.totalReferrals);
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
        <div className="w-full max-w-sm">
            {/* Referral Stats */}
            <div className="bg-[#2C2C2C] rounded-lg p-4 mb-4">
                <h3 className="text-white text-lg mb-3">Your Referrals</h3>
                <div className="grid grid-cols-3 gap-4">
                    <div>
                        <p className="text-[#F7AA1C] text-2xl">{referralStats.totalReferrals}</p>
                        <p className="text-[#ffffff]/60 text-sm">Total</p>
                    </div>
                    <div>
                        <p className="text-[#F7AA1C] text-2xl">{referralStats.tokensEarned}</p>
                        <p className="text-[#ffffff]/60 text-sm">Tokens Earned</p>
                    </div>
                    <div>
                        <p className="text-[#F7AA1C] text-2xl">{referralStats.pendingReferrals}</p>
                        <p className="text-[#ffffff]/60 text-sm">Pending</p>
                    </div>
                </div>
            </div>

            {/* Share Button */}
            <button 
                onClick={shareReferral}
                className="w-full flex justify-center items-center gap-2 text-lg px-7 py-4 text-[#BEBEBE] border border-[#F7AA1C] shadow-[0_0_9px_rgba(247,170,28,0.3)] transition-all duration-200 rounded-[35px] hover:shadow-[0_0_12px_rgba(247,170,28,0.7)]"
            >
                <Share2 className="w-5 h-5" />
                Share & Earn
            </button>

            {/* Share Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-[#1C1C1C] rounded-lg p-6 w-96">
                        <h2 className="text-white text-xl mb-4">Share Your Referral Code</h2>
                        <div className="bg-[#2C2C2C] p-3 rounded-lg flex justify-between items-center mb-4">
                            <span className="text-white font-mono">{referralCode}</span>
                            <button 
                                onClick={copyToClipboard}
                                className="text-[#F7AA1C] hover:text-[#d89116]"
                            >
                                {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                            </button>
                        </div>
                        <div className="flex justify-end">
                            <button 
                                onClick={() => setIsModalOpen(false)}
                                className="px-4 py-2 text-white border border-gray-600 rounded hover:bg-gray-700"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ShareReferral;