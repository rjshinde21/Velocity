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
// router.get('/plan', authMiddleware, userController.getUserPlan);

// Token routes
// router.get('/tokens', authMiddleware, tokenController.getAllTokens);
// router.get('/tokens/:id', authMiddleware, tokenController.getTokenById); // Added proper route for getting token by ID

module.exports = router;