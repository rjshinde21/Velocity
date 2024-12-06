// controllers/history.controller.js
const db = require('../config/database');

const historyController = {
    // Save original prompt
    savePrompt :async (req, res) => {
        try {
            const { prompt_text, ai_type, tokens_used = 0, user_id } = req.body;
            
            console.log('Received request body:', req.body); // Debug log
    
            // Additional input validation
            if (!user_id || !prompt_text || !ai_type) {
                console.log('Missing required fields:', { user_id, prompt_text, ai_type }); // Debug log
                return res.status(400).json({
                    success: false,
                    message: 'Missing required fields',
                    details: {
                        user_id: !user_id ? 'missing' : 'present',
                        prompt_text: !prompt_text ? 'missing' : 'present',
                        ai_type: !ai_type ? 'missing' : 'present'
                    }
                });
            }
    
            const query = `
                INSERT INTO prompt_history 
                (user_id, content_type, prompt_text, ai_type, tokens_used) 
                VALUES (?, 'input_prompt', ?, ?, ?)
            `;
    
            const params = [user_id, prompt_text, ai_type, tokens_used];
            console.log('Query params:', params); // Debug log
    
            const [result] = await db.execute(query, params);
    
            res.status(201).json({
                success: true,
                data: {
                    history_id: result.insertId,
                    user_id,
                    prompt_text,
                    ai_type,
                    tokens_used,
                    created_at: new Date()
                }
            });
        } catch (error) {
            console.error('Database error:', error); // Debug log
            res.status(500).json({
                success: false,
                message: 'Failed to save prompt',
                error: error.message,
                details: req.body
            });
        }
    },

    // Save copied response
    saveResponse: async (req, res) => {
        try {
            const { prompt_text, original_prompt_id, ai_type, user_id } = req.body;

            // Validate required fields
            if (!user_id) {
                return res.status(400).json({
                    success: false,
                    message: 'User ID is required in request body'
                });
            }

            if (!prompt_text || !original_prompt_id || !ai_type) {
                return res.status(400).json({
                    success: false,
                    message: 'Prompt text, original prompt ID, and AI type are required'
                });
            }

            const query = `
                INSERT INTO prompt_history 
                (user_id, content_type, prompt_text, original_prompt_id, ai_type) 
                VALUES (?, 'copied_response', ?, ?, ?)
            `;

            const [result] = await db.execute(query, [
                user_id,
                prompt_text,
                original_prompt_id,
                ai_type
            ]);

            res.status(201).json({
                success: true,
                data: {
                    history_id: result.insertId,
                    user_id,
                    prompt_text,
                    original_prompt_id,
                    ai_type,
                    created_at: new Date()
                }
            });
        } catch (error) {
            console.error('Error saving response:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to save response',
                error: error.message,
                details: {
                    body: req.body
                }
            });
        }
    },

    // Get user's history
    getUserHistory: async (req, res) => {
        try {
            const { user_id } = req.query;  // Changed from params to query
            const { type, limit = 50, offset = 0 } = req.query;

            if (!user_id) {
                return res.status(400).json({
                    success: false,
                    message: 'User ID is required in query parameters'
                });
            }

            let query = `
                SELECT 
                    h.*, 
                    original.prompt_text as original_prompt
                FROM prompt_history h
                LEFT JOIN prompt_history original 
                    ON h.original_prompt_id = original.history_id
                WHERE h.user_id = ? 
                    AND h.is_deleted = FALSE
            `;

            if (type) {
                query += ` AND h.content_type = ?`;
            }

            query += ` ORDER BY h.created_at DESC LIMIT ? OFFSET ?`;
            
            const params = type 
                ? [user_id, type, parseInt(limit), parseInt(offset)]
                : [user_id, parseInt(limit), parseInt(offset)];
            //console.log("query:"+query +"and params:" + params);
            const [results] = await db.execute(query, params);

            res.json({
                success: true,
                data: results
            });
        } catch (error) {
            console.error('Error fetching history:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to fetch history',
                error: error.message
            });
        }
    },

    // Toggle favorite status
    toggleFavorite: async (req, res) => {
        try {
            const { historyId } = req.params;
            const { user_id } = req.body;

            if (!user_id) {
                return res.status(400).json({
                    success: false,
                    message: 'User ID is required in request body'
                });
            }

            const query = `
                UPDATE prompt_history 
                SET is_favorited = NOT is_favorited 
                WHERE history_id = ? AND user_id = ?
            `;

            const [result] = await db.execute(query, [historyId, user_id]);

            if (result.affectedRows === 0) {
                return res.status(404).json({
                    success: false,
                    message: 'History item not found'
                });
            }

            res.json({
                success: true,
                message: 'Favorite status toggled successfully'
            });
        } catch (error) {
            console.error('Error toggling favorite:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to toggle favorite status',
                error: error.message
            });
        }
    },

    // Soft delete history item
    deleteHistoryItem: async (req, res) => {
        try {
            const { historyId } = req.params;
            const { user_id } = req.body;

            if (!user_id) {
                return res.status(400).json({
                    success: false,
                    message: 'User ID is required in request body'
                });
            }

            const query = `
                UPDATE prompt_history 
                SET is_deleted = TRUE 
                WHERE history_id = ? AND user_id = ?
            `;

            const [result] = await db.execute(query, [historyId, user_id]);

            if (result.affectedRows === 0) {
                return res.status(404).json({
                    success: false,
                    message: 'History item not found'
                });
            }

            res.json({
                success: true,
                message: 'History item deleted successfully'
            });
        } catch (error) {
            console.error('Error deleting history item:', error);
            res.status(500).json({
                success: false,
                message: 'Failed to delete history item',
                error: error.message
            });
        }
    }
};

module.exports = historyController;