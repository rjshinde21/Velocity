class PromptHistory {
    constructor(apiBaseUrl = 'http://localhost:5000') {
        this.API_BASE_URL = apiBaseUrl;
        this.historyPanel = null;
        this.historyButton = null;
    }

    initialize(containerSelector = '.scrollable-container', afterElementSelector = '.radio-group') {
        this.createHistoryButton();
        this.createHistoryPanel();
        
        const container = document.querySelector(containerSelector);
        const afterElement = document.querySelector(afterElementSelector);
        
        if (container && afterElement) {
            container.appendChild(this.historyPanel);
            afterElement.after(this.historyButton);
            this.loadHistory();
        } else {
            console.error('Required DOM elements not found');
        }

        // Add necessary styles
        this.addStyles();
    }

    createHistoryButton() {
        this.historyButton = document.createElement('button');
        this.historyButton.className = 'icon-button history-button';
        this.historyButton.innerHTML = `
            <img src="./assets/history.png" alt="History" class="button-icon">
            <span>Prompt History</span>
        `;
        
        this.historyButton.addEventListener('click', () => {
            this.historyPanel.classList.toggle('hidden2');
            this.loadHistory();
        });
    }

    createHistoryPanel() {
        this.historyPanel = document.createElement('div');
        this.historyPanel.id = 'historyPanel';
        this.historyPanel.className = 'history-panel hidden2';
        this.historyPanel.innerHTML = `
            <div class="history-header">
                <h3>Prompt History</h3>
            </div>
            <div class="history-list"></div>
        `;
    }

    async loadHistory() {
        const historyList = this.historyPanel.querySelector('.history-list');
        if (!historyList) return;
        
        try {
            const response = await fetch(`${this.API_BASE_URL}/history`, {
                credentials: 'include'
            });
            const data = await response.json();
            
            historyList.innerHTML = '';
            data.history.forEach(item => {
                const historyItem = this.createHistoryItem(item);
                historyList.appendChild(historyItem);
            });
        } catch (error) {
            console.error('Error loading history:', error);
            historyList.innerHTML = '<div class="error-message">Failed to load history</div>';
        }
    }

    createHistoryItem(item) {
        const container = document.createElement('div');
        container.className = 'history-item';
        
        const categories = JSON.parse(item.categories || '{}');
        const date = new Date(item.created_at).toLocaleDateString();
        
        container.innerHTML = `
            <div class="history-item-content">
                <div class="history-item-header">
                    <span class="history-date">${date}</span>
                    <span class="history-ai-type">${item.ai_type}</span>
                </div>
                <div class="history-prompt">${item.prompt_text}</div>
                <div class="history-categories">
                    ${Object.entries(categories)
                        .map(([key, value]) => `<span class="category-tag">${key}: ${value}</span>`)
                        .join('')}
                </div>
                <div class="history-actions">
                    <button class="reuse-prompt" data-prompt-id="${item.prompt_id}">
                        <img src="./assets/reuse.png" alt="Reuse" class="action-icon">
                    </button>
                    <button class="delete-prompt" data-prompt-id="${item.prompt_id}">
                        <img src="./assets/delete.png" alt="Delete" class="action-icon">
                    </button>
                </div>
            </div>
        `;
        
        container.querySelector('.reuse-prompt').addEventListener('click', () => this.reusePrompt(item));
        container.querySelector('.delete-prompt').addEventListener('click', () => this.deletePrompt(item.prompt_id));
        
        return container;
    }

    async savePrompt(promptData) {
        try {
            const response = await fetch(`${this.API_BASE_URL}/history/save`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(promptData)
            });
            
            const data = await response.json();
            if (!data.success) {
                console.error('Failed to save prompt to history:', data.error);
            }
        } catch (error) {
            console.error('Error saving to history:', error);
        }
    }

    reusePrompt(item) {
        const promptInput = document.getElementById('promptInput');
        if (promptInput) {
            promptInput.value = item.prompt_text;
            
            // Set AI type
            const radioButtons = document.querySelectorAll('.radio-button');
            radioButtons.forEach(button => {
                if (button.textContent.trim() === item.ai_type) {
                    button.click();
                }
            });
            
            // Set categories
            const categories = JSON.parse(item.categories || '{}');
            Object.entries(categories).forEach(([category, value]) => {
                const categoryCard = document.querySelector(`.category-card .category-title:contains('${category}')`);
                if (categoryCard) {
                    const dropdown = categoryCard.closest('.category-card').querySelector('.dropdown');
                    const option = dropdown.querySelector(`button:contains('${value}')`);
                    if (option) {
                        option.click();
                    }
                }
            });
        }
    }

    async deletePrompt(promptId) {
        if (confirm('Are you sure you want to delete this prompt?')) {
            try {
                const response = await fetch(`${this.API_BASE_URL}/history/${promptId}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });
                
                const data = await response.json();
                if (data.success) {
                    this.loadHistory();
                } else {
                    throw new Error(data.error || 'Failed to delete prompt');
                }
            } catch (error) {
                console.error('Error deleting prompt:', error);
                alert('Failed to delete prompt');
            }
        }
    }

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            /* Add your CSS styles here */
            .history-button {
                margin-top: 10px;
                width: 100%;
                background-color: #0906299e;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px;
                cursor: pointer;
                transition: background-color 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .history-panel {
                background-color: rgba(0, 0, 0, 0.4);
                border: 1px solid #444;
                border-radius: 10px;
                margin-top: 10px;
                padding: 15px;
                max-height: 400px;
                overflow-y: auto;
            }

            /* Add the rest of your CSS styles here */
        `;
        document.head.appendChild(style);
    }
}

// Export the class
export default PromptHistory;