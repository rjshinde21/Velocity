const LaunchList = require('../models/launchlist.model');
const { validationResult } = require('express-validator');

class LaunchListController {
    static async subscribe(req, res) {
        try {
            // Check for validation errors
            const errors = validationResult(req);
            if (!errors.isEmpty()) {
                return res.status(400).json({ 
                    success: false,
                    errors: errors.array() 
                });
            }

            const { email } = req.body;

            // Check if email already exists
            const existingUser = await LaunchList.findByEmail(email);
            if (existingUser) {
                return res.status(409).json({
                    success: false,
                    message: 'This email is already registered'
                });
            }

            // Create new subscription
            await LaunchList.create(email);

            return res.status(201).json({
                success: true,
                message: 'Successfully added to launch list',
                data: { email }
            });

        } catch (error) {
            console.error('Error in subscribe:', error);
            return res.status(500).json({
                success: false,
                message: 'Internal server error'
            });
        }
    }

    static async getSubscribersCount(req, res) {
        try {
            const count = await LaunchList.getCount();
            return res.status(200).json({
                success: true,
                data: { count }
            });
        } catch (error) {
            console.error('Error in getSubscribersCount:', error);
            return res.status(500).json({
                success: false,
                message: 'Internal server error'
            });
        }
    }
}

module.exports = LaunchListController;