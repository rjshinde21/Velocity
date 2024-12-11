// referralController.js
const db = require('../config/database');
const crypto = require('crypto');
const Token = require('../models/token.model');

const generateReferralCode = async (req, res) => {
    const { user_id } = req.body;
    let connection;
    
    try {
        connection = await db.getConnection();
        await connection.beginTransaction();

        // Check if user already has a referral code
        const [existingCode] = await connection.query(
            'SELECT code FROM referral_codes WHERE user_id = ?',
            [user_id]
        );

        if (existingCode.length > 0) {
            await connection.commit();
            return res.json({ 
                success: true,
                referralCode: existingCode[0].code 
            });
        }

        // Generate new unique referral code
        let code;
        let isUnique = false;
        while (!isUnique) {
            code = crypto.randomBytes(5).toString('hex').toUpperCase();
            const [existing] = await connection.query(
                'SELECT code FROM referral_codes WHERE code = ?',
                [code]
            );
            if (existing.length === 0) {
                isUnique = true;
            }
        }

        // Store new referral code
        await connection.query(
            'INSERT INTO referral_codes (code, user_id) VALUES (?, ?)',
            [code, user_id]
        );

        await connection.commit();
        res.json({ 
            success: true,
            referralCode: code 
        });
    } catch (error) {
        if (connection) {
            await connection.rollback();
        }
        console.error('Error generating referral code:', error);
        res.status(500).json({ 
            success: false,
            error: 'Failed to generate referral code' 
        });
    } finally {
        if (connection) {
            connection.release();
        }
    }
};

const applyReferral = async (req, res) => {
    const { referral_code, new_user_id } = req.body;
    let connection;
    
    try {
        connection = await db.getConnection();
        await connection.beginTransaction();

        // Verify referral code and get referrer
        const [referralData] = await connection.query(
            'SELECT user_id FROM referral_codes WHERE code = ?',
            [referral_code]
        );

        if (referralData.length === 0) {
            await connection.rollback();
            return res.status(400).json({ 
                success: false,
                error: 'Invalid referral code' 
            });
        }

        const referrer_id = referralData[0].user_id;
        const REFERRER_BONUS = 50; // Tokens for referrer
        const REFERRED_BONUS = 30; // Tokens for new user

        // Create referral record
        await connection.query(
            `INSERT INTO referrals 
             (referrer_id, referred_id, referral_code, tokens_awarded_referrer, tokens_awarded_referred, status) 
             VALUES (?, ?, ?, ?, ?, 'completed')`,
            [referrer_id, new_user_id, referral_code, REFERRER_BONUS, REFERRED_BONUS]
        );

        // Update referral code usage count
        await connection.query(
            'UPDATE referral_codes SET times_used = times_used + 1 WHERE code = ?',
            [referral_code]
        );
        await Token.topUpTokens(referrer_id, REFERRER_BONUS, connection);
        await Token.topUpTokens(new_user_id, REFERRED_BONUS, connection);

        // Top up tokens for both users using the Token model
        // try {
        //     // Update referrer's tokens
        //     await Token.topUpTokens(referrer_id, REFERRER_BONUS, connection);
            
        //     // Update referred user's tokens
        //     await Token.topUpTokens(new_user_id, REFERRED_BONUS, connection);
        // } catch (error) {
        //     throw new Error(`Failed to update tokens: ${error.message}`);
        // }

        await connection.commit();
        res.json({ 
            success: true, 
            message: 'Referral applied successfully',
            tokensAwarded: {
                referred: REFERRED_BONUS,
                referrer: REFERRER_BONUS
            }
        });
    } catch (error) {
        if (connection) {
            await connection.rollback();
        }
        console.error('Error applying referral:', error);
        res.status(500).json({ 
            success: false,
            error: 'Failed to apply referral: ' + error.message
        });
    } finally {
        if (connection) {
            connection.release();
        }
    }
};


const getReferralStats = async (req, res) => {
    const { user_id } = req.params;
    
    try {
        const [stats] = await db.query(
            `SELECT 
                COUNT(r.referral_id) as totalReferrals,
                SUM(r.tokens_awarded_referrer) as tokensEarned,
                COUNT(CASE WHEN r.status = 'pending' THEN 1 END) as pendingReferrals
             FROM referrals r
             WHERE r.referrer_id = ?`,
            [user_id]
        );

        const [recentReferrals] = await db.query(
            `SELECT 
                u.name as referred_name,
                r.created_at,
                r.tokens_awarded_referrer
             FROM referrals r
             JOIN usertable u ON u.user_id = r.referred_id
             WHERE r.referrer_id = ?
             ORDER BY r.created_at DESC
             LIMIT 5`,
            [user_id]
        );

        res.json({
            success: true,
            data: {
                stats: stats[0],
                recentReferrals
            }
        });
    } catch (error) {
        console.error('Error fetching referral stats:', error);
        res.status(500).json({ 
            success: false,
            error: 'Failed to fetch referral stats' 
        });
    }
};


module.exports = {
    generateReferralCode,
    applyReferral,
    getReferralStats
};