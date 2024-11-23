# Prompt History Module

A self-contained module for adding prompt history functionality to Chrome extensions.

## Package Structure
```
prompt-history-module/
├── backend/
│   ├── __init__.py
│   ├── prompt_history_module.py
│   ├── integrate_history.py
│   └── requirements.txt
├── frontend/
│   ├── history.js
│   ├── history.css
│   └── assets/
│       ├── history.png
│       ├── reuse.png
│       └── delete.png
├── database/
│   └── init_db.py
├── README.md
└── INSTALL.md
```

## Quick Start

1. Backend Setup
```bash
cd your-extension/backend
pip install -r requirements.txt
python init_db.py
```

2. Frontend Integration
```javascript
// In your popup.js
import { PromptHistory } from './modules/history.js';
const history = new PromptHistory();
history.initialize();
```

See INSTALL.md for detailed installation instructions.