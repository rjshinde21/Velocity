const jwt = require('jsonwebtoken');

const authMiddleware = (req, res, next) => {
  // console.log("checking"+req.headers.authorization);
  try {
    const token = req.headers.authorization?.split(' ')[1];
    // console.log("token:"+token);
    if (!token) {
      return res.status(401).json({ message: 'Authentication required' });
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.userId = decoded.userId;
    next();
  } catch (error) {
    res.status(401).json({ message: 'Invalid token' });
  }
};

module.exports = authMiddleware;