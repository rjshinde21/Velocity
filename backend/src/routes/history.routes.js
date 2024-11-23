// routes/history.routes.js
const express = require('express');
const router = express.Router();
const historyController = require('../controllers/history.controller');
const historyValidation = require('../validations/history.validation');

router.post('/prompts', 
    historyValidation.createPrompt, 
    historyController.savePrompt
);

router.post('/responses', 
    historyValidation.saveResponse, 
    historyController.saveResponse
);

router.get('/user/history', 
    historyValidation.getUserHistory, 
    historyController.getUserHistory
);

router.patch('/favorite/:historyId', 
    historyValidation.validateHistoryId, 
    historyController.toggleFavorite
);

router.delete('/:historyId', 
    historyValidation.validateHistoryId, 
    historyController.deleteHistoryItem
);

module.exports = router;