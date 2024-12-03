const Token = require('../models/token.model');
const Razorpay = require('razorpay');
const crypto = require('crypto');

const razorpay = new Razorpay({
    key_id: process.env.RAZORPAY_KEY_ID,
    key_secret: process.env.RAZORPAY_KEY_SECRET
});

const tokenController = {
    async getAllTokens(req, res) {
        try {
            const tokens = await Token.getAllTokens();
            res.status(200).json({
                success: true,
                data: tokens
            });
        } catch (error) {
            console.error('Error fetching tokens:', error);
            res.status(500).json({
                success: false,
                message: 'Error fetching tokens',
                error: error.message
            });
        }
    },

    async getTokenById(req, res) {
        try {
            const id = parseInt(req.params.id);
            console.log('Requesting token with ID:', id);

            if (isNaN(id)) {
                return res.status(400).json({
                    success: false,
                    message: 'Invalid token ID format'
                });
            }

            const token = await Token.getTokenById(id);
            console.log('Token found:', token);

            if (!token) {
                return res.status(404).json({
                    success: false,
                    message: `Token with ID ${id} not found`
                });
            }
            console.log("returning");
            return res.status(200).json({
                success: true,
                data: token
            });
        } catch (error) {
            console.error('Error fetching token:', error);
            return res.status(500).json({
                success: false,
                message: 'Error fetching token',
                error: error.message
            });
        }
    },

    async updateTokens(req, res) {
        try {
            // Extract the user ID from the request parameters
            const id = parseInt(req.params.id);
            console.log("body:"+req.body);
            const { token_received, tokens_used } = req.body;
    
            // Validate if ID is a valid number
            if (isNaN(id)) {
                return res.status(400).json({
                    success: false,
                    message: 'Invalid token ID format',
                });
            }
    
            // Validate token_received and tokens_used
            if (token_received < 0 || tokens_used < 0) {
                return res.status(400).json({
                    success: false,
                    message: 'Token values must be non-negative',
                });
            }
    
            // Calculate tokens left
            const tokensLeft = token_received - tokens_used;
    
            // Ensure tokens_used does not exceed tokens_received
            if (tokensLeft < 0) {
                return res.status(400).json({
                    success: false,
                    message: 'Invalid token values: tokens used cannot exceed tokens received',
                });
            }
    
            // Update the tokens in the database
            const result = await Token.updateTokens(id, token_received, tokens_used);
    
            // Check if any rows were updated
            if (result.affectedRows === 0) {
                return res.status(404).json({
                    success: false,
                    message: `Token with ID ${id} not found`,
                });
            }
    
            // Respond with a success message and updated data
            res.status(200).json({
                success: true,
                message: `Tokens updated for ID ${id}`,
                data: {
                    token_received,
                    tokens_used,
                    tokens_left: tokensLeft, // Include tokens left in the response
                },
            });
        } catch (error) {
            console.error('Error updating tokens:', error);
            res.status(500).json({
                success: false,
                message: 'Error updating tokens',
                error: error.message,
            });
        }
    },
    async topUpTokens(req, res) {
        try {
            const id = parseInt(req.params.id);
            const { amount } = req.body;
    
            // Validate ID
            if (isNaN(id)) {
                return res.status(400).json({
                    success: false,
                    message: 'Invalid token ID format'
                });
            }
    
            // Validate amount
            if (!amount || amount <= 0) {
                return res.status(400).json({
                    success: false,
                    message: 'Top-up amount must be a positive number'
                });
            }
    
            // Perform the top-up
            await Token.topUpTokens(id, amount);
    
            // Get updated token information
            const updatedToken = await Token.getTokenById(id);
    
            res.status(200).json({
                success: true,
                message: `Successfully topped up ${amount} tokens`,
                data: updatedToken
            });
    
        } catch (error) {
            console.error('Error topping up tokens:', error);
            res.status(500).json({
                success: false,
                message: 'Error topping up tokens',
                error: error.message
            });
        }
    },
    async createOrder(req, res){
        try {
            const options = {
                amount: req.body.amount,
                currency: 'INR',
                receipt: 'order_' + Date.now(),
            };
    
            const order = await razorpay.orders.create(options);
            res.json(order);
        } catch (error) {
            res.status(500).json({ message: 'Error creating order', error: error.message });
        }
    },
    
    async verifyPayment(req, res) {
        console.log("verifying:"+req.body);
        try {
            const {
                razorpay_payment_id,
                razorpay_order_id,
                razorpay_signature,
                amount,
                userId
            } = req.body;
    
            const body = razorpay_order_id + "|" + razorpay_payment_id;
            const expectedSignature = crypto
                .createHmac("sha256", process.env.RAZORPAY_KEY_SECRET)
                .update(body.toString())
                .digest("hex");
    
            if (expectedSignature === razorpay_signature) {
                // Payment is verified, now update tokens
                //const userId = req.user.id; // Assuming you have user info in req from auth middleware
                await Token.topUpTokens(userId, amount);
                
                res.json({
                    success: true,
                    message: 'Payment verified successfully'
                });
            } else {
                res.status(400).json({
                    success: false,
                    message: 'Invalid signature'
                });
            }
        } catch (error) {
            res.status(500).json({
                success: false,
                message: 'Error verifying payment',
                error: error.message
            });
        }
    }
    
};




module.exports = tokenController;