# Detailed Installation Guide

## Prerequisites
- Python 3.7+
- Flask backend
- Chrome Extension with popup functionality

## Step 1: Backend Setup

1. Copy the `backend` folder to your project:
```bash
cp -r prompt-history-module/backend/* your-project/backend/
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python init_db.py
```

4. Update your Flask app:
```python
from flask import Flask
from integrate_history import integrate_history

app = Flask(__name__)
integrate_history(app)  # This adds all history endpoints
```

## Step 2: Frontend Setup

1. Copy the frontend module:
```bash
cp -r prompt-history-module/frontend/* your-project/extension/modules/
```

2. Copy assets:
```bash
cp -r prompt-history-module/frontend/assets/* your-project/extension/assets/
```

3. Add CSS to your extension:
```html
<!-- In popup.html -->
<link rel="stylesheet" href="modules/history.css">
```

4. Import and initialize the module:
```javascript
// In popup.js
import { PromptHistory } from './modules/history.js';

document.addEventListener('DOMContentLoaded', function() {
    const history = new PromptHistory('http://localhost:5000');
    history.initialize();

    // Integrate with your existing send function
    const originalSendRequest = window.sendRequest;
    window.sendRequest = async function() {
        const result = await originalSendRequest();
        if (result.success) {
            await history.savePrompt({
                prompt: document.getElementById('promptInput').value,
                ai_type: getSelectedRadioValue(),
                categories: getSelectedCategories()
            });
        }
        return result;
    };
});
```

## Step 3: Configuration

1. Update manifest.json:
```json
{
  "permissions": [
    "storage",
    "cookies"
  ],
  "host_permissions": [
    "http://localhost:5000/*"
  ]
}
```

2. Configure backend URL:
```javascript
// In popup.js
const history = new PromptHistory('your-backend-url');
```

## Troubleshooting

### Common Issues

1. CORS Errors
```python
# In your Flask app
from flask_cors import CORS
CORS(app, resources={
    r"/history/*": {
        "origins": ["chrome-extension://*"],
        "supports_credentials": True
    }
})
```

2. Database Issues
```bash
# Reset database
python init_db.py --reset
```

3. Missing Assets
Check if all required images are in the correct location:
- history.png
- reuse.png
- delete.png

### Support

For issues and support, contact [Your Contact Info]