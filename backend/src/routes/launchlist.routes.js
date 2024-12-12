const express = require('express');
const router = express.Router();
const LaunchListController = require('../controllers/launchlist.controller');
const launchListValidation = require('../validations/launchlist.validation');

router.post(
    '/subscribe', 
    launchListValidation.subscribe,
    LaunchListController.subscribe
);

router.get(
    '/count',
    LaunchListController.getSubscribersCount
);

module.exports = router;