const CreditModel = require('../models/credit.model');

const CreditController = {
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
  }
};

module.exports = CreditController;