const Joi = require('joi');

const validateFeatureRestrictions = (req, res, next) => {
  const schema = Joi.object({
    free_user_daily_limit: Joi.number().integer().min(0).required(),
    free_user_timeout_minutes: Joi.number().integer().min(0).required(),
    is_restricted_for_free: Joi.boolean().required()
  });

  const { error } = schema.validate(req.body);
  if (error) {
    return res.status(400).json({ 
      success: false, 
      error: error.details[0].message 
    });
  }
  next();
};

module.exports = {
  validateFeatureRestrictions
};
