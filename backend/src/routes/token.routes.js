const express = require('express');
const router = express.Router();
const tokenController = require('../controllers/token.controller');
const authMiddleware = require('../middleware/auth.middleware');

// Get all tokens
router.get('/token-types', authMiddleware, tokenController.getAllTokens);
// Get token by ID - Changed the route to match your requirement
router.get('/token-types/:id', authMiddleware, tokenController.getTokenById);
// Update tokens by ID
router.put('/token-types/:id', authMiddleware, tokenController.updateTokens);

module.exports = router;