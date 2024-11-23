const express = require('express');
const router = express.Router();
const CreditController = require('../controllers/credit.controller');
const authMiddleware = require('../middleware/auth.middleware');
const { validateFeatureRestrictions } = require('../validations/credit.validation');

// Existing routes
router.get('/credits', authMiddleware, CreditController.getCredits);
router.get('/:id', authMiddleware, CreditController.getCreditById);
router.get('/credits/feature/:feature', authMiddleware, CreditController.getCreditsByFeature);

// New routes for free user restrictions
router.put(
  '/credits/:id/restrictions',
  authMiddleware,
  validateFeatureRestrictions,
  CreditController.updateFeatureRestrictions
);
router.post(
  '/credits/:featureId/access',
  authMiddleware,
  CreditController.checkFeatureAccess
);
router.post('/use/:featureId', authMiddleware, CreditController.useFeature);

module.exports = router;
