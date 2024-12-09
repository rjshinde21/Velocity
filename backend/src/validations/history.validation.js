const Joi = require('joi');

const historyValidation = {
    createPrompt: async (req, res, next) => {
        const schema = Joi.object({
            user_id: Joi.alternatives().try(
                Joi.number(),
                Joi.string()
            ).required().messages({
                'any.required': 'User ID is required',
                'any.only': 'Invalid user ID format'
            }),
            prompt_text: Joi.string().required().messages({
                'any.required': 'Prompt text is required',
                'string.empty': 'Prompt text cannot be empty'
            }),
            tokens_used: Joi.number().min(0).default(0).messages({
                'number.base': 'Tokens used must be a number',
                'number.min': 'Tokens used cannot be negative'
            })
        }).options({ stripUnknown: true });

        try {
            console.log('Validating request body:', req.body); // Debug log
            const value = await schema.validateAsync(req.body);
            console.log('Validated value:', value); // Debug log
            req.body = value;
            next();
        } catch (error) {
            console.error('Validation error details:', error.details); // Debug log
            res.status(400).json({
                success: false,
                message: 'Validation error',
                errors: error.details.map(detail => ({
                    field: detail.path[0],
                    message: detail.message,
                    value: detail.context.value
                }))
            });
        }
    },



    saveResponse: async (req, res, next) => {
        const schema = Joi.object({
            user_id: Joi.alternatives().try(
                Joi.number(),
                Joi.string()
            ).required().messages({
                'any.required': 'User ID is required',
                'any.only': 'Invalid user ID format'
            }),
            prompt_text: Joi.string().required().messages({
                'any.required': 'Prompt text is required',
                'string.empty': 'Prompt text cannot be empty'
            }),
            original_prompt_id: Joi.alternatives().try(
                Joi.number(),
                Joi.string()
            ).required().messages({
                'any.required': 'Original prompt ID is required'
            }),
            tokens_used: Joi.number().min(0).default(0).messages({
                'number.base': 'Tokens used must be a number',
                'number.min': 'Tokens used cannot be negative'
            })
        }).options({ stripUnknown: true });

        try {
            console.log('Validating copied response body:', req.body); // Debug log
            const value = await schema.validateAsync(req.body);
            console.log('Validated copied response value:', value); // Debug log
            req.body = value;
            next();
        } catch (error) {
            console.error('Copied response validation error:', error.details); // Debug log
            res.status(400).json({
                success: false,
                message: 'Validation error',
                errors: error.details.map(detail => ({
                    field: detail.path[0],
                    message: detail.message,
                    value: detail.context.value
                }))
            });
        }
    },

    getUserHistory: async (req, res, next) => {
        const schema = Joi.object({
            user_id: Joi.number().integer().required()
                .messages({
                    'any.required': 'User ID is required',
                    'number.base': 'User ID must be a number'
                }),
            type: Joi.string().valid('input_prompt', 'copied_response').optional()
                .messages({
                    'any.only': 'Type must be either input_prompt or copied_response'
                }),
            limit: Joi.number().integer().min(1).max(100).default(50)
                .messages({
                    'number.base': 'Limit must be a number',
                    'number.min': 'Limit must be at least 1',
                    'number.max': 'Limit cannot exceed 100'
                }),
            offset: Joi.number().integer().min(0).default(0)
                .messages({
                    'number.base': 'Offset must be a number',
                    'number.min': 'Offset cannot be negative'
                })
        });

        try {
            const value = await schema.validateAsync(req.query, { abortEarly: false });
            // Replace query parameters with validated values
            req.query = value;
            next();
        } catch (error) {
            res.status(400).json({
                success: false,
                message: 'Validation error',
                errors: error.details.map(detail => ({
                    field: detail.path[0],
                    message: detail.message
                }))
            });
        }
    },

    validateHistoryId: async (req, res, next) => {
        const schema = Joi.object({
            historyId: Joi.number().integer().required()
                .messages({
                    'any.required': 'History ID is required',
                    'number.base': 'History ID must be a number'
                }),
            user_id: Joi.number().integer().required()
                .messages({
                    'any.required': 'User ID is required',
                    'number.base': 'User ID must be a number'
                })
        });

        try {
            const params = { 
                historyId: parseInt(req.params.historyId),
                user_id: req.body.user_id 
            };
            
            const value = await schema.validateAsync(params, { abortEarly: false });
            // Add validated values back to request
            req.params.historyId = value.historyId;
            req.body.user_id = value.user_id;
            next();
        } catch (error) {
            res.status(400).json({
                success: false,
                message: 'Validation error',
                errors: error.details.map(detail => ({
                    field: detail.path[0],
                    message: detail.message
                }))
            });
        }
    }
};

module.exports = historyValidation;