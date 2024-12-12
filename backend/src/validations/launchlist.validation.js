const { body } = require('express-validator');

const launchListValidation = {
    subscribe: [
        body('email')
            .trim()
            .isEmail()
            .withMessage('Please enter a valid email address')
            .normalizeEmail()
            .toLowerCase()
    ]
};

module.exports = launchListValidation;