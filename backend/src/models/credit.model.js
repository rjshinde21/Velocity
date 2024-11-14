const db = require('../config/database');


const CreditModel = {
  async getAllCredits() {
    const [rows] = await db.query('SELECT * FROM credits');
    return rows;
  },

  async getCreditById(id) {
    const [rows] = await db.query('SELECT * FROM credits WHERE id = ?', [id]);
    return rows[0];
  },

  async getCreditsByFeature(feature) {
    const [rows] = await db.query('SELECT * FROM credits WHERE feature = ?', [feature]);
    return rows;
  }
};

module.exports = CreditModel;