const express = require('express');
const router = express.Router();
const CreditController = require('../controllers/credit.controller');
const authMiddleware = require('../middleware/auth.middleware');

router.get('/credits', authMiddleware, CreditController.getCredits);
router.get('/:id', authMiddleware, CreditController.getCreditById);
router.get('/credits/feature/:feature', authMiddleware, CreditController.getCreditsByFeature);

module.exports = router;