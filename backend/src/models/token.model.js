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

    static async updateTokens(id, token_received, tokens_used) {
        // Calculate tokens left
        const tokens_left = token_received - tokens_used;

        console.log("ID:", id);
        console.log("Token Received:", token_received);
        console.log("Tokens Used:", tokens_used);
        console.log("Tokens Left:", tokens_left);

        try {
            const [result] = await db.query(
                `
                UPDATE tokentable t
                JOIN usertable u ON t.user_id = u.user_id
                SET t.token_received = ?, t.tokens_used = ?, u.tokens = ?
                WHERE t.user_id = ?
                `,
                [token_received, tokens_used, tokens_left, id]
            );

            console.log("Update Result:", result);

            // If no rows were updated, throw an error
            if (result.affectedRows === 0) {
                throw new Error(`No record found for user_id ${id}`);
            }

            return result;
        } catch (error) {
            console.error("Error updating tokens:", error.message);
            throw error;
        }
    }
    

    static async getTokenByUserId(userId) {
        const [rows] = await db.query('SELECT * FROM tokentable WHERE user_id = ?', [userId]);
        return rows[0];
    }
}

module.exports = Token;