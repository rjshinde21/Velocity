// models/user.model.js
const db = require('../config/database');
const bcrypt = require('bcryptjs');

class User {
    static async create(userData) {
        try {
            const { name, email, password, plan_id = 1, tokens = 50 } = userData;
            // Using bcryptjs for consistent hashing
            const salt = await bcrypt.genSalt(10);
            const hashedPassword = await bcrypt.hash(password, salt);
            
            const query = `
                INSERT INTO usertable 
                (name, email, password, plan_id, tokens) 
                VALUES (?, ?, ?, ?, ?)
            `;
            const [result] = await db.query(query, [name, email, hashedPassword, plan_id, tokens]);
            return result.insertId;
        } catch (error) {
            console.error('Error creating user:', error);
            throw error;
        }
    }

    static async findByEmail(email) {
        try {
            // Ensure we're selecting all fields including password
            const query = 'SELECT * FROM usertable WHERE email = ?';
            const [rows] = await db.query(query, [email]);
            return rows[0];
        } catch (error) {
            console.error('Error finding user by email:', error);
            throw error;
        }
    }

    static async findById(user_id) {
        try {
            const query = `
                SELECT id, name, email, plan_id, tokens, created_at 
                FROM usertable 
                WHERE user_id = ?
            `;
            const [rows] = await db.query(query, [id]);
            return rows[0];
        } catch (error) {
            console.error('Error finding user by id:', error);
            throw error;
        }
    }

    static async update(user_id, userData) {
        try {
            const { name, email } = userData;
            const query = 'UPDATE usertable SET name = ?, email = ? WHERE user_id = ?';
            const [result] = await db.query(query, [name, email, user_id]);
            return result.affectedRows > 0;
        } catch (error) {
            console.error('Error updating user:', error);
            throw error;
        }
    }

    static async updatePlan(id, plan_id) {
        try {
            const query = 'UPDATE usertable SET plan_id = ? WHERE id = ?';
            const [result] = await db.query(query, [plan_id, id]);
            return result.affectedRows > 0;
        } catch (error) {
            console.error('Error updating plan:', error);
            throw error;
        }
    }

    static async updateTokens(user_id, tokens) {
        try {
            const query = 'UPDATE usertable SET tokens = ? WHERE user_id = ?';
            const [result] = await db.query(query, [tokens, user_id]);
            return result.affectedRows > 0;
        } catch (error) {
            console.error('Error updating tokens:', error);
            throw error;
        }
    }

    static async delete(id) {
        try {
            const query = 'DELETE FROM usertable WHERE id = ?';
            const [result] = await db.query(query, [id]);
            return result.affectedRows > 0;
        } catch (error) {
            console.error('Error deleting user:', error);
            throw error;
        }
    }

    // static async getUserPlan(plan_id) {
    //     try {
    //         const query = 'SELECT plan_id FROM usertable WHERE user_id = ?';
    //         const [rows] = await db.query(query, [plan_id]);
    //         return rows[0]?.plan_id;
    //     } catch (error) {
    //         console.error('Error getting user plan:', error);
    //         throw error;
    //     }
    // }

    static async getTokens(user_id) {
        try {
            const query = 'SELECT tokens FROM usertable WHERE user_id = ?';
            const [rows] = await db.query(query, [user_id]);
            return rows[0]?.tokens || 0;
        } catch (error) {
            console.error('Error getting tokens:', error);
            throw error;
        }
    }
}

module.exports = User;