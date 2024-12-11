const router = require('express').Router();
const referralController = require('../controllers/referralController');
const authMiddleware = require('../middleware/auth.middleware');

router.post('/generate', authMiddleware, referralController.generateReferralCode);
router.post('/apply', authMiddleware, referralController.applyReferral);
router.get('/stats/:user_id', authMiddleware, referralController.getReferralStats);

module.exports = router;
