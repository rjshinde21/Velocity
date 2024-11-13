const db = require('../config/database');

class Plan {
    static async getAllPlans() {
        try {
            const query = `
                SELECT 
                    plan_id,
                    plan_name,
                    token_received,
                    cost
                FROM plantable
                ORDER BY cost ASC
            `;
            const [rows] = await db.query(query);
            return rows;
        } catch (error) {
            console.error('Error fetching plans:', error);
            throw error;
        }
    }

    static async getPlanById(id) {
        try {
            const query = `
                SELECT 
                    plan_id,
                    plan_name,
                    token_received,
                    cost
                FROM plantable
                WHERE plan_id = ?
            `;
            const [rows] = await db.query(query, [id]);
            return rows[0] || null;
        } catch (error) {
            console.error('Error fetching plan by ID:', error);
            throw error;
        }
    }

    static async updatePlan(userId, newPlanId) {
        try {
            // console.log('Updating plan for user:', userId, 'to plan:', newPlanId);

            // First check if user exists
            const userQuery = 'SELECT user_id FROM usertable WHERE user_id = ?';
            const [userResult] = await db.query(userQuery, [userId]);

            if (!userResult || userResult.length === 0) {
                throw new Error('User not found');
            }

            // Update user's plan_id
            const query = `
                UPDATE usertable 
                SET 
                    plan_id = ?,
                    updated_at = CURRENT_TIMESTAMP 
                WHERE user_id = ?
            `;
            
            const [result] = await db.query(query, [newPlanId, userId]);

            if (result.affectedRows === 0) {
                throw new Error('Failed to update plan');
            }

            // Get updated user data
            const updatedUserQuery = `
                SELECT 
                    u.user_id,
                    u.name,
                    u.email,
                    u.tokens,
                    p.plan_id,
                    p.plan_name,
                    p.token_received,
                    p.cost
                FROM usertable u
                JOIN plantable p ON u.plan_id = p.plan_id
                WHERE u.user_id = ?
            `;
            
            const [updatedUser] = await db.query(updatedUserQuery, [userId]);
            return updatedUser[0];

        } catch (error) {
            console.error('Error updating plan:', error);
            throw error;
        }
    }

    static async getActivePlanUsers(planId) {
        try {
            const query = `
                SELECT COUNT(*) as userCount
                FROM usertable
                WHERE plan_id = ?
            `;
            const [rows] = await db.query(query, [planId]);
            return rows[0].userCount;
        } catch (error) {
            console.error('Error getting plan users count:', error);
            throw error;
        }
    }

    static async getUserPlan(userId) {
        try {
            const query = `
                SELECT 
                    u.user_id,
                    u.name,
                    u.email,
                    u.tokens,
                    p.plan_id,
                    p.plan_name,
                    p.token_received,
                    p.cost
                FROM usertable u
                JOIN plantable p ON u.plan_id = p.plan_id
                WHERE u.user_id = ?
            `;
            
            const [rows] = await db.query(query, [userId]);
            return rows[0] || null;
        } catch (error) {
            console.error('Error fetching user plan:', error);
            throw error;
        }
    }
    
}

module.exports = Plan;