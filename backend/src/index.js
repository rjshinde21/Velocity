const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');
const userRoutes = require('./routes/user.routes');
const tokenRoutes = require('./routes/token.routes');
const planRoutes = require('./routes/plan.routes');
const creditRoutes = require('./routes/credit.route');
require('dotenv').config();

const app = express();




// This should be at the top of your app.js/index.js
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
// Configure CORS
app.use(cors({
    origin: ['https://www.toteminteractive.in', 'http://127.0.0.1:3000', 'http://localhost:5173', 'http://localhost:3000'],
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'Accept'],
    credentials: true,
    optionsSuccessStatus: 200
}));

// Add CORS headers middleware
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', 'https://www.toteminteractive.in','http://127.0.0.1:3000','http://localhost:5173');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
    res.header('Access-Control-Allow-Credentials', true);
    
    // Handle preflight requests
    if (req.method === 'OPTIONS') {
        return res.sendStatus(200);
    }
    next();
});

// Middleware
app.use(express.json());

// Database connection
const connection = mysql.createConnection({
    host: process.env.DB_HOST || 'localhost',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || 'velocity@321',
    database: process.env.DB_NAME || 'velocitydb'
});

// Routes
app.use('/api/users', userRoutes);
app.use('/api', tokenRoutes);
app.use('/api/plans', planRoutes);
app.use('/api/credit', creditRoutes);

const PORT = process.env.PORT || 3000;

// Initialize database and start server
async function initializeApp() {
    try {
        // Test database connection
        await connection.promise().connect();
        console.log('Connected to database successfully');

        // Start server
        app.listen(PORT, () => {
            console.log(`Server is running on port ${PORT}`);
        });
    } catch (error) {
        console.error('Failed to initialize app:', error);
        process.exit(1);
    }
}

initializeApp();

// Export connection for use in other files
module.exports = connection;