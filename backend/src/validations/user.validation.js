// validations/user.validation.js
const { body } = require('express-validator');
const validate = require('../middleware/validation.middleware');

const userValidation = {
    register: [
        body('name')
            .trim()
            .isLength({ min: 3 })
            .withMessage('Name must be at least 3 characters'),
        body('email')
            .isEmail()
            .withMessage('Must be a valid email')
            .normalizeEmail(),
        body('password')
            .isLength({ min: 6 })
            .withMessage('Password must be at least 6 characters'),
        body('plan_id')
            .optional()
            .isInt({ min: 1 })
            .withMessage('Invalid plan ID'),
        validate
    ],

    login: [
        body('email')
            .isEmail()
            .withMessage('Must be a valid email')
            .normalizeEmail(),
        body('password')
            .exists()
            .withMessage('Password is required'),
        validate
    ],

    update: [
        body('name')
            .optional()
            .trim()
            .isLength({ min: 3 })
            .withMessage('Name must be at least 3 characters'),
        body('email')
            .optional()
            .isEmail()
            .withMessage('Must be a valid email')
            .normalizeEmail(),
        validate
    ],

    updatePlan: [
        body('plan_id')
            .isInt({ min: 1 })
            .withMessage('Invalid plan ID'),
        validate
    ]
};

module.exports = userValidation;