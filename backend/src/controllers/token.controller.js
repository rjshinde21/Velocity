const Token = require('../models/token.model');

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
            // console.log('Requesting token with ID:', id);

            if (isNaN(id)) {
                return res.status(400).json({
                    success: false,
                    message: 'Invalid token ID format'
                });
            }

            const token = await Token.getTokenById(id);
            // console.log('Token found:', token);

            if (!token) {
                return res.status(404).json({
                    success: false,
                    message: `Token with ID ${id} not found`
                });
            }

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
            const id = parseInt(req.params.id);
            const { token_received, tokens_used } = req.body;

            if (isNaN(id)) {
                return res.status(400).json({
                    success: false,
                    message: 'Invalid token ID format'
                });
            }

            // Update the tokens
            const result = await Token.updateTokens(id, token_received, tokens_used);

            if (result.affectedRows === 0) {
                return res.status(404).json({
                    success: false,
                    message: `Token with ID ${id} not found`
                });
            }

            res.status(200).json({
                success: true,
                message: `Tokens updated for ID ${id}`
            });
        } catch (error) {
            console.error('Error updating tokens:', error);
            res.status(500).json({
                success: false,
                message: 'Error updating tokens',
                error: error.message
            });
        }
    }
};

module.exports = tokenController;