const db = require('../config/database');

const CreditModel = {
  // Existing methods
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
  },

  // New methods for free user restrictions
  async updateFeatureRestrictions(id, { free_user_daily_limit, free_user_timeout_minutes, is_restricted_for_free }) {
    const [result] = await db.query(
      `UPDATE credits 
       SET free_user_daily_limit = ?, 
           free_user_timeout_minutes = ?, 
           is_restricted_for_free = ?
       WHERE id = ?`,
      [free_user_daily_limit, free_user_timeout_minutes, is_restricted_for_free, id]
    );
    return result.affectedRows > 0;
  },

  async checkUserFeatureUsage(userId, featureId) {
    // Get feature details
    const [feature] = await db.query(
      'SELECT * FROM credits WHERE id = ?',
      [featureId]
    );

    if (!feature[0]) {
      throw new Error('Feature not found');
    }

    // Get usage count for last 24 hours
    const [usage] = await db.query(
      `SELECT COUNT(*) as count 
       FROM feature_usage 
       WHERE user_id = ? 
       AND feature_id = ? 
       AND used_at > NOW() - INTERVAL 24 HOUR`,
      [userId, featureId]
    );

    // Get last usage timestamp
    const [lastUsage] = await db.query(
      `SELECT used_at 
       FROM feature_usage 
       WHERE user_id = ? 
       AND feature_id = ? 
       ORDER BY used_at DESC 
       LIMIT 1`,
      [userId, featureId]
    );

    return {
      feature: feature[0],
      usageCount: usage[0].count,
      lastUsage: lastUsage[0]?.used_at
    };
  },
  async checkFeatureAccess(userId, featureId) {
    try {
        const [feature] = await db.query(
            'SELECT * FROM credits WHERE id = ?', 
            [featureId]
        );

        if (!feature.length) {
            return {
                success: false,
                message: 'Feature not found'
            };
        }

        // If feature isn't restricted for free users, allow access
        if (!feature[0].is_restricted_for_free) {
            return {
                success: true,
                data: { canUse: true }
            };
        }

        // Get current usage count
        const [usageCount] = await db.query(
            `SELECT COUNT(*) as count 
             FROM feature_usage 
             WHERE user_id = ? 
             AND feature_id = ? 
             AND used_at > NOW() - INTERVAL 24 HOUR`,
            [userId, featureId]
        );

        // Get last usage to check timeout
        const [lastUsage] = await db.query(
            `SELECT used_at 
             FROM feature_usage 
             WHERE user_id = ? 
             AND feature_id = ? 
             ORDER BY used_at DESC 
             LIMIT 1`,
            [userId, featureId]
        );

        const count = usageCount[0].count;

        // Check timeout if limit was reached
        if (count >= feature[0].free_user_daily_limit && lastUsage.length > 0) {
            const timeoutUntil = new Date(lastUsage[0].used_at.getTime() + 
                feature[0].free_user_timeout_minutes * 60000);
            
            if (timeoutUntil > new Date()) {
                return {
                    success: true,
                    data: {
                        canUse: false,
                        reason: 'timeout',
                        timeoutUntil,
                        usageCount: count,
                        dailyLimit: feature[0].free_user_daily_limit
                    }
                };
            } else {
                // Timeout expired - reset usage count
                await db.query(
                    `DELETE FROM feature_usage 
                     WHERE user_id = ? 
                     AND feature_id = ?`,
                    [userId, featureId]
                );
                
                return {
                    success: true,
                    data: {
                        canUse: true,
                        usageCount: 0,
                        dailyLimit: feature[0].free_user_daily_limit
                    }
                };
            }
        }

        // Regular limit check
        return {
            success: true,
            data: {
                canUse: count < feature[0].free_user_daily_limit,
                usageCount: count,
                dailyLimit: feature[0].free_user_daily_limit
            }
        };
    } catch (error) {
        return {
            success: false,
            message: error.message
        };
    }
},
async resetFeatureUsage(userId, featureId) {
  try {
      const [result] = await db.query(
          `DELETE FROM feature_usage 
           WHERE user_id = ? 
           AND feature_id = ?`,
          [userId, featureId]
      );
      return result.affectedRows > 0;
  } catch (error) {
      throw error;
  }
},
  async recordFeatureUsage(userId, featureId) {
    try {
      const [result] = await db.query(
        'INSERT INTO feature_usage (user_id, feature_id) VALUES (?, ?)',
        [userId, featureId]
      );
      return result.insertId;
    } catch (error) {
      throw error;
    }
  }

};

module.exports = CreditModel;
