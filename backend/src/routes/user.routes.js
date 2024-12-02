const express = require('express');
const router = express.Router();
const userController = require('../controllers/user.controller');
// const tokenController = require('../controllers/token.controller');
const authMiddleware = require('../middleware/auth.middleware');
const userValidation = require('../validations/user.validation');

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
      const token = req.headers.authorization?.split(' ')[1];
      
      if (!token) {
        return res.status(401).json({
          success: false,
          message: 'No token provided'
        });
      }
  
      // Verify the token using your JWT secret
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      
      // Optional: Check if user still exists in database
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
      return res.status(401).json({
        success: false,
        message: 'Invalid token'
      });
    }
  });
// router.get('/plan', authMiddleware, userController.getUserPlan);

// Token routes
// router.get('/tokens', authMiddleware, tokenController.getAllTokens);
// router.get('/tokens/:id', authMiddleware, tokenController.getTokenById); // Added proper route for getting token by ID

module.exports = router;