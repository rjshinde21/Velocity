const User = require('../models/user.model');
const Token = require('../models/token.model');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const db = require('../config/database');

// Define constants
const INITIAL_TOKEN_AMOUNT = 50;

const userController = {
    async register(req, res) {
        console.log("Registration request:", req.body);
        try {
            const { name, email, password, googleId, avatar } = req.body;
            
            // Validate email presence
            if (!email) {
                return res.status(400).json({ 
                    success: false,
                    message: 'Email is required' 
                });
            }

            // For regular sign-up, require password
            if (!googleId && !password) {
                return res.status(400).json({ 
                    success: false,
                    message: 'Password is required for regular sign-up' 
                });
            }

            // Email validation
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                return res.status(400).json({ 
                    success: false,
                    message: 'Please provide a valid email address' 
                });
            }

            // Check if user exists
            const [existingUsers] = await db.query(
                'SELECT * FROM usertable WHERE email = ? OR google_id = ?',
                [email, googleId]
            );

            if (existingUsers && existingUsers.length > 0) {
                return res.status(409).json({
                    success: false,
                    message: 'User already exists'
                });
            }

            // Start a transaction
            const connection = await db.getConnection();
            await connection.beginTransaction();

            try {
                // Insert user with or without Google ID
                let hashedPassword = null;
                if (password) {
                    hashedPassword = await bcrypt.hash(password, 10);
                }

                const [userResult] = await connection.query(
                    `INSERT INTO usertable 
                    (name, email, password, google_id, tokens) 
                    VALUES (?, ?, ?, ?, ?)`,
                    [name, email, hashedPassword, googleId || null, INITIAL_TOKEN_AMOUNT]
                );

                const userId = userResult.insertId;

                // Create token record
                const [tokenResult] = await connection.query(
                    `INSERT INTO tokentable (
                        token_received, 
                        tokens_used, 
                        boughtDateTime,
                        expiryDateTime,
                        user_id
                    ) VALUES (?, ?, CURRENT_TIMESTAMP, DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 1 YEAR), ?)`,
                    [INITIAL_TOKEN_AMOUNT, 0, userId]
                );

                await connection.commit();

                // Generate JWT token
                const authToken = jwt.sign(
                    { userId, email },
                    process.env.JWT_SECRET || 'your_jwt_secret_key',
                    { expiresIn: '24h' }
                );

                res.status(201).json({
                    success: true,
                    message: 'User registered successfully',
                    data: {
                        user: {
                            id: userId,
                            name,
                            email,
                            avatar
                        },
                        token: authToken,
                        tokenInfo: {
                            id: tokenResult.insertId,
                            token_received: INITIAL_TOKEN_AMOUNT,
                            tokens_used: 0
                        }
                    }
                });

            } catch (error) {
                await connection.rollback();
                throw error;
            } finally {
                connection.release();
            }

        } catch (error) {
            console.error('Registration error:', error);
            res.status(500).json({
                success: false,
                message: 'Error registering user',
                error: error.message
            });
        }
    },

    async login(req, res) {
        try {
            const { email, password, googleId } = req.body;
            
            if (!email) {
                return res.status(400).json({
                    success: false,
                    message: 'Email is required'
                });
            }

            // Find user by email or Google ID
            let queryString = 'SELECT * FROM usertable WHERE email = ?';
            let queryParams = [email];

            if (googleId) {
                queryString = 'SELECT * FROM usertable WHERE email = ? OR google_id = ?';
                queryParams = [email, googleId];
            }

            const [users] = await db.query(queryString, queryParams);
            const user = users[0];

            if (!user) {
                return res.status(404).json({
                    success: false,
                    message: 'User not found'
                });
            }

            // Validate based on auth type
            if (googleId) {
                // For Google login, update google_id if not present
                if (!user.google_id) {
                    await db.query(
                        'UPDATE usertable SET google_id = ? WHERE user_id = ?',
                        [googleId, user.user_id]
                    );
                }
            } else {
                // Regular login
                if (!password || !user.password) {
                    return res.status(401).json({
                        success: false,
                        message: 'Invalid credentials'
                    });
                }
                const validPassword = await bcrypt.compare(password, user.password);
                if (!validPassword) {
                    return res.status(401).json({
                        success: false,
                        message: 'Invalid credentials'
                    });
                }
            }

            // Generate token
            const token = jwt.sign(
                { userId: user.user_id },
                process.env.JWT_SECRET || 'your-secret-key',
                { expiresIn: '24h' }
            );

            res.json({
                success: true,
                message: 'Login successful',
                data: {
                    token,
                    user: {
                        id: user.user_id,
                        name: user.name,
                        email: user.email,
                        avatar: user.avatar
                    }
                }
            });
        } catch (error) {
            console.error('Login error:', error);
            res.status(500).json({
                success: false,
                message: 'Error during login',
                error: error.message
            });
        }
    },

    async getProfile(req, res) {         
        try {             
            // console.log("Request parameters:", req.params); // Debug req.params
    
            const id = req.params.id;             
            // console.log("User ID from request:", id); // Should log the user ID if defined
    
            if (!id) {
                return res.status(400).json({ 
                    success: false, 
                    message: 'User ID is required' 
                });
            }
    
            // Using MySQL query to get user from usertable             
            const [rows] = await db.query(
                'SELECT user_id, name, email, plan_id, tokens FROM usertable WHERE user_id = ?', 
                [id]
            );
    
            // Check if user exists             
            if (!rows || rows.length === 0) {                 
                console.log("User not found for ID:", id);                 
                return res.status(404).json({                     
                    success: false,                     
                    message: 'User not found'                 
                });             
            }        
    
            const user = rows[0];                  
    
            // Get token information             
            const [tokenRows] = await db.query(
                'SELECT token_received, tokens_used, boughtDateTime, expiryDateTime FROM tokentable WHERE user_id = ?', 
                [id]
            );
    
            const tokenInfo = tokenRows[0] || null;                  
    
            // Fix the response to use the correct field names             
            res.json({                 
                success: true,                 
                data: {                     
                    user: {                         
                        user_id: user.user_id,                         
                        name: user.name,                         
                        email: user.email,
                        plan_id: user.plan_id,                         
                        tokens: user.tokens                     
                    },                     
                    tokenInfo: tokenInfo                 
                }             
            });         
        } catch (error) {             
            console.error('Profile fetch error:', error);             
            res.status(500).json({                 
                success: false,                 
                message: 'Error fetching profile',                 
                error: error.message             
            });         
        }     
    },
    

    async updateProfile(req, res) {
        try {
            const { name, email } = req.body;
            
            if (!name && !email) {
                return res.status(400).json({
                    success: false,
                    message: 'Please provide at least one field to update'
                });
            }

            const success = await User.update(req.userId, { name, email });

            if (!success) {
                return res.status(404).json({
                    success: false,
                    message: 'User not found'
                });
            }

            res.json({
                success: true,
                message: 'Profile updated successfully'
            });
        } catch (error) {
            res.status(500).json({
                success: false,
                message: 'Error updating profile',
                error: error.message
            });
        }
    },

    async deleteProfile(req, res) {
        try {
            const userId = req.params.id;
            const connection = await db.getConnection();
            await connection.beginTransaction();

            try {
                // Delete token records first
                await connection.query('DELETE FROM tokentable WHERE user_id = ?', [userId]);
                
                // Then delete user
                const [result] = await connection.query('DELETE FROM usertable WHERE user_id = ?', [req.userId]);
                
                if (result.affectedRows === 0) {
                    await connection.rollback();
                    return res.status(404).json({
                        success: false,
                        message: 'User not found'
                    });
                }

                await connection.commit();

                res.json({
                    success: true,
                    message: 'Profile deleted successfully'
                });
            } catch (error) {
                await connection.rollback();
                throw error;
            } finally {
                connection.release();
            }
        } catch (error) {
            res.status(500).json({
                success: false,
                message: 'Error deleting profile',
                error: error.message
            });
        }
    },

    async updatePlan(req, res) {
        try {
            const { plan } = req.body;
            if (!plan) {
                return res.status(400).json({
                    success: false,
                    message: 'Please provide a plan'
                });
            }
            const updated = await User.updatePlan(req.userId, plan);
            if (!updated) {
                return res.status(404).json({
                    success: false,
                    message: 'User not found'
                });
            }
            res.json({
                success: true,
                message: 'Plan updated successfully',
                data: { plan }
            });
        } catch (error) {
            console.error('Plan update error:', error);
            res.status(500).json({
                success: false,
                message: 'Error updating plan',
                error: error.message
            });
        }
    },

    // async getUserPlan(req, res) {
    //     try {
    //         const plan = await User.getUserPlan(req.userId);
            
    //         if (!plan) {
    //             return res.status(404).json({
    //                 success: false,
    //                 message: 'User not found'
    //             });
    //         }

    //         res.json({
    //             success: true,
    //             data: { plan }
    //         });
    //     } catch (error) {
    //         console.error('Plan fetch error:', error);
    //         res.status(500).json({
    //             success: false,
    //             message: 'Error fetching plan',
    //             error: error.message
    //         });
    //     }
    // },

    async getTokens(req, res) {
        try {
            const [tokenRecord] = await db.query(
                'SELECT * FROM tokentable WHERE user_id = ?',
                [req.userId]
            );

            if (!tokenRecord) {
                return res.status(404).json({
                    success: false,
                    message: 'Token record not found'
                });
            }

            res.json({
                success: true,
                data: {
                    token_received: tokenRecord.token_received,
                    tokens_used: tokenRecord.tokens_used,
                    boughtDateTime: tokenRecord.boughtDateTime,
                    expiryDateTime: tokenRecord.expiryDateTime
                }
            });
        } catch (error) {
            
            console.error('Tokens fetch error:', error);
            res.status(500).json({
                success: false,
                message: 'Error fetching tokens',
                error: error.message
            });
        }
    }
    
};

module.exports = userController;