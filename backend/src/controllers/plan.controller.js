const Plan = require('../models/plan.model');

const planController = {
    async getAllPlans(req, res) {
        try {
            const plans = await Plan.getAllPlans();
            res.status(200).json({
                success: true,
                data: plans
            });
        } catch (error) {
            console.error('Error fetching plans:', error);
            res.status(500).json({
                success: false,
                message: 'Error fetching plans',
                error: error.message
            });
        }
    },

    async getPlanById(req, res) {
        try {
            const id = parseInt(req.params.id);
            
            if (isNaN(id)) {
                return res.status(400).json({
                    success: false,
                    message: 'Invalid plan ID format'
                });
            }

            const plan = await Plan.getPlanById(id);
            
            if (!plan) {
                return res.status(404).json({
                    success: false,
                    message: 'Plan not found'
                });
            }

            // Get number of users using this plan
            const userCount = await Plan.getActivePlanUsers(id);

            res.status(200).json({
                success: true,
                data: {
                    ...plan,
                    active_users: userCount
                }
            });
        } catch (error) {
            console.error('Error fetching plan:', error);
            res.status(500).json({
                success: false,
                message: 'Error fetching plan',
                error: error.message
            });
        }
    },

    async updatePlan(req, res) {
        try {
            const userId = req.params.id;  // Get user ID from auth middleware
            const newPlanId = 2;  // Set to premium plan ID

            console.log('Updating plan for user:', userId, 'to premium plan');

            // Update the plan
            const updatedUser = await Plan.updatePlan(userId, newPlanId);

            if (!updatedUser) {
                return res.status(400).json({
                    success: false,
                    message: 'Failed to update plan'
                });
            }

            return res.status(200).json({
                success: true,
                message: 'Plan updated successfully',
                data: {
                    user_id: updatedUser.user_id,
                    name: updatedUser.name,
                    email: updatedUser.email,
                    current_tokens: updatedUser.tokens,
                    plan: {
                        plan_id: updatedUser.plan_id,
                        plan_name: updatedUser.plan_name,
                        token_received: updatedUser.token_received,
                        cost: updatedUser.cost
                    }
                }
            });

        } catch (error) {
            console.error('Error updating plan:', error);
            return res.status(500).json({
                success: false,
                message: error.message || 'Error updating plan',
                error: error.message
            });
        }
    },
    
    async getUserPlan (req, res) {
        try {
            const userId = req.params.userId;
            const userPlan = await Plan.getUserPlan(userId);
            // console.log('Retrieved User Plan:', userPlan);
            // console.log('Retrieved User Id:', userId);

    
            if (!userPlan) {
                return res.status(404).json({
                    success: false,
                    message: 'User not found'
                });
            }
    
            return res.status(200).json({
                success: true,
                message: 'User plan fetched successfully',
                data: {
                    user_id: userPlan.user_id,
                    name: userPlan.name,
                    email: userPlan.email,
                    current_tokens: userPlan.tokens,
                    plan: {
                        plan_id: userPlan.plan_id,
                        plan_name: userPlan.plan_name,
                        token_received: userPlan.token_received,
                        cost: userPlan.cost
                    }
                }
            });
        } catch (error) {
            console.error('Error in getUserPlan:', error);
            return res.status(500).json({
                success: false,
                message: 'Internal server error',
                error: error.message
            });
        }
    
}
};

module.exports = planController;