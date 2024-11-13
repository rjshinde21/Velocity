const express = require('express');
const router = express.Router();
const planController = require('../controllers/plan.controller');
const authMiddleware = require('../middleware/auth.middleware');

// Get all plans
router.get('/', authMiddleware, planController.getAllPlans);

// Get specific plan by ID
router.get('/:id', authMiddleware, planController.getPlanById);

// Update plan
router.put('/:id', authMiddleware, planController.updatePlan);

router.get('/user/plan/:userId', authMiddleware, planController.getUserPlan);

module.exports = router;