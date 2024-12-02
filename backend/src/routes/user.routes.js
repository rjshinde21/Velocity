const express = require('express');
const router = express.Router();
const userController = require('../controllers/user.controller');
// const tokenController = require('../controllers/token.controller');
const authMiddleware = require('../middleware/auth.middleware');
const userValidation = require('../validations/user.validation');
const jwt = require('jsonwebtoken');
const User = require('../models/user.model');

// Public routes
router.post('/register', userValidation.register, userController.register);
router.post('/login', userValidation.login, userController.login);

// Protected routes
router.get('/profile/:id', authMiddleware, userController.getProfile);
router.put('/profile/:id', authMiddleware, userValidation.update, userController.updateProfile);
router.delete('/profile/:id', authMiddleware, userController.deleteProfile);

// Plan management routes
router.put('/plan', authMiddleware, userValidation.updatePlan, userController.updatePlan);

router.post('/verify-token', async (req, res) => {
  try {
    const authHeader = req.headers.authorization;
    console.log('Received auth header:', authHeader); // Debug log

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        success: false,
        message: 'No token provided or invalid format'
      });
    }

    const token = authHeader.split(' ')[1];
    console.log('Extracting token:', token); // Debug log

    // Verify the token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    console.log('Decoded token:', decoded); // Debug log

    // Check if user exists in database
    const user = await User.findById(decoded.userId);
    if (!user) {
      return res.status(401).json({
        success: false,
        message: 'User not found'
      });
    }

    return res.status(200).json({
      success: true,
      message: 'Token is valid',
      data: {
        user: {
          id: user._id,
          email: user.email,
          name: user.name
        }
      }
    });
  } catch (error) {
    console.error('Token verification error:', error);
    return res.status(401).json({
      success: false,
      message: error.message || 'Invalid token'
    });
  }
});

// router.get('/plan', authMiddleware, userController.getUserPlan);

// Token routes
// router.get('/tokens', authMiddleware, tokenController.getAllTokens);
// router.get('/tokens/:id', authMiddleware, tokenController.getTokenById); // Added proper route for getting token by ID

module.exports = router;