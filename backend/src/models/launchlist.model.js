const db = require('../config/database.js');

class LaunchList {
    static async create(email) {
        const query = 'INSERT INTO launch_list (email) VALUES (?)';
        try {
            const [result] = await db.execute(query, [email]);
            return result;
        } catch (error) {
            throw error;
        }
    }

    static async findByEmail(email) {
        const query = 'SELECT * FROM launch_list WHERE email = ?';
        try {
            const [rows] = await db.execute(query, [email]);
            return rows[0];
        } catch (error) {
            throw error;
        }
    }

    static async getCount() {
        const query = 'SELECT COUNT(*) as count FROM launch_list';
        try {
            const [rows] = await db.execute(query);
            return rows[0].count;
        } catch (error) {
            throw error;
        }
    }
}

module.exports = LaunchList;