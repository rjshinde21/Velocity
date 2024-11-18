// token.model.js
const db = require('../config/database');

class Token {
    static async getAllTokens() {
        const [rows] = await db.query('SELECT * FROM tokentable');
        return rows;
    }

    static async getTokenById(id) {
        const [rows] = await db.query('SELECT * FROM tokentable WHERE user_id = ?', [id]);
        return rows[0];
    }

    static async updateTokens(user_id, token_received, tokens_used) {
        // Calculate tokens_left
        const tokens_left = token_received - tokens_used;
    console.log("user id:"+ user_id);
    console.log("token_received:"+ token_received);
    console.log("tokens used:"+ tokens_used);
    console.log("tokens left:"+ tokens_left);
        try {
            const [result] = await db.query(
                `
                UPDATE tokentable t
                JOIN usertable u ON t.user_id = u.user_id
                SET t.token_received = ?, t.tokens_used = ?, u.tokens = ?
                WHERE t.user_id = ?
                `,
                [token_received, tokens_used, tokens_left, user_id]
            );
            console.log('Update result:', result);
    
            // If no rows were updated, throw an error
            if (result.affectedRows === 0) {
                throw new Error(`No record found for user_id ${user_id}`);
            }
    
            return result;
        } catch (error) {
            console.error('Error updating tokens:', error);
            throw error; // Rethrow the error to be handled by the calling function
        }
    }
    

    static async getTokenByUserId(userId) {
        const [rows] = await db.query('SELECT * FROM tokentable WHERE user_id = ?', [userId]);
        return rows[0];
    }
}

module.exports = Token;