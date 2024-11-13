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
        const [result] = await db.query(
            'UPDATE tokentable SET token_received = ?, tokens_used = ? WHERE user_id = ?',
            [token_received, tokens_used, id]
        );
        return result;
    }

    static async getTokenByUserId(userId) {
        const [rows] = await db.query('SELECT * FROM tokentable WHERE user_id = ?', [userId]);
        return rows[0];
    }
}

module.exports = Token;