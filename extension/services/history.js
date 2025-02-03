class HistoryService {
    static async savePromptToHistory(promptText, aiType) {
        try {
          const storage = await chrome.storage.local.get(['userId', 'token']);
          const userId = storage.userId;
          const token = storage.token;
      
          if (!userId || !token) {
            throw new Error('User authentication required');
          }
      
          // Ensure aiType is a string
          const aiTypeString = String(aiType || 'General');
      
          const response = await fetch('https://thinkvelocity.in/api/api/history/prompts', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
              user_id: userId,
              prompt_text: promptText,
              ai_type: aiTypeString,  // Convert to string
              tokens_used: 0
            })
          });
      
          const data = await response.json();
          if (!data.success) {
            throw new Error(data.message);
          }
      
          return data;
        } catch (error) {
          // console.error('Error saving prompt to history:', error);
          throw error;
        }
      }

      static async saveResponseToHistory(promptText, originalPromptId, aiType, tokensUsed) {
        try {
          const storage = await chrome.storage.local.get(['userId', 'token']);
          const userId = storage.userId;
          const token = storage.token;
      
          if (!userId || !token) {
            throw new Error('User authentication required');
          }
      
          // Ensure aiType is a string
          const aiTypeString = String(aiType || 'General');
      
          const response = await fetch('https://thinkvelocity.in/api/api/history/responses', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
              user_id: userId,
              prompt_text: promptText,
              original_prompt_id: originalPromptId,
              ai_type: aiTypeString,  // Convert to string
              tokens_used: tokensUsed || 0
            })
          });
      
          const data = await response.json();
          if (!data.success) {
            throw new Error(data.message);
          }
      
          return data;
        } catch (error) {
          // console.error('Error saving response to history:', error);
          throw error;
        }
      }
    
}