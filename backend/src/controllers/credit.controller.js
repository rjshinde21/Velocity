const CreditModel = require('../models/credit.model');

const CreditController = {
  // Existing methods
  async getCredits(req, res) {
    try {
      const credits = await CreditModel.getAllCredits();
      res.json({ success: true, data: credits });
    } catch (error) {
      res.status(500).json({ success: false, error: error.message });
    }
  },

  async getCreditById(req, res) {
    try {
      const { id } = req.params;
      const credit = await CreditModel.getCreditById(id);
      
      if (!credit) {
        return res.status(404).json({ success: false, message: 'Credit not found' });
      }
      
      res.json({ success: true, data: credit });
    } catch (error) {
      res.status(500).json({ success: false, error: error.message });
    }
  },

  async getCreditsByFeature(req, res) {
    try {
      const { feature } = req.params;
      const credits = await CreditModel.getCreditsByFeature(feature);
      
      if (!credits.length) {
        return res.status(404).json({ success: false, message: 'No credits found for this feature' });
      }
      
      res.json({ success: true, data: credits });
    } catch (error) {
      res.status(500).json({ success: false, error: error.message });
    }
  },

  // New methods for free user restrictions
  async updateFeatureRestrictions(req, res) {
    try {
      const { id } = req.params;
      const { free_user_daily_limit, free_user_timeout_minutes, is_restricted_for_free } = req.body;

      const updated = await CreditModel.updateFeatureRestrictions(id, {
        free_user_daily_limit,
        free_user_timeout_minutes,
        is_restricted_for_free
      });

      if (!updated) {
        return res.status(404).json({ success: false, message: 'Feature not found' });
      }

      const credit = await CreditModel.getCreditById(id);
      res.json({ success: true, data: credit });
    } catch (error) {
      res.status(500).json({ success: false, error: error.message });
    }
  },

  async checkFeatureAccess(req, res) {
    try {
      const userId = req.body.userId; // Changed to get from body instead of auth
      const { featureId } = req.params;

      if (!userId) {
        return res.status(400).json({ 
          success: false, 
          message: 'userId is required in request body' 
        });
      }

      const { feature, usageCount, lastUsage } = await CreditModel.checkUserFeatureUsage(userId, featureId);
      console.log("usage count:"+usageCount);
      console.log("daily limit:"+feature.free_user_daily_limit);
      // If feature isn't restricted for free users, allow access
      if (!feature.is_restricted_for_free) {
        return res.json({ 
          success: true, 
          data: { canUse: true } 
        });
      }

      // Check timeout if daily limit was reached
      if (usageCount >= feature.free_user_daily_limit && lastUsage) {
        console.log("going inside if");
        const timeoutUntil = new Date(lastUsage.getTime() + feature.free_user_timeout_minutes * 60000);
        
        if (timeoutUntil > new Date()) {
          return res.json({
            success: true,
            data: {
              canUse: false,
              reason: 'timeout',
              timeoutUntil
            }
          });
        }
      }
      console.log("helo");
      res.json({
        success: true,
        data: {
          canUse: usageCount < feature.free_user_daily_limit,
          usageCount,
          dailyLimit: feature.free_user_daily_limit
        }
      });
    } catch (error) {
      res.status(500).json({ success: false, error: error.message });
    }
  },

  async useFeature(req, res) {
    try {
      const userId = req.body.userId;
      const { featureId } = req.params;

      if (!userId) {
        return res.status(400).json({ 
          success: false, 
          message: 'userId is required in request body' 
        });
      }

      // First check if user can use the feature
      const accessCheck = await CreditModel.checkFeatureAccess(userId, featureId);

      if (!accessCheck.canUse) {
        return res.json({
          success: false,
          message: accessCheck.reason === 'timeout' 
            ? `Feature locked until ${accessCheck.timeoutUntil}` 
            : `Daily limit reached (${accessCheck.usageCount}/${accessCheck.dailyLimit})`,
          data: accessCheck
        });
      }

      // If they can use it, record the usage
      await CreditModel.recordFeatureUsage(userId, featureId);

      // Return success with updated usage info
      const updatedAccess = await CreditModel.checkFeatureAccess(userId, featureId);
      res.json({
        success: true,
        message: 'Feature usage recorded',
        data: updatedAccess
      });

    } catch (error) {
      res.status(500).json({ 
        success: false, 
        error: error.message 
      });
    }
  }
};
module.exports = CreditController;
