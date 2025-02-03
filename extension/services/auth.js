class AuthService {

    static async checkAuthState() {
        if (isDiscordPlatform()) {
          console.log('Skipping auth state check for Discord');
          return null;
        }
      
        if (!isValidPlatform) {
          return null;
        }
      
    
        const authData = {
          isAuthenticated: !!localStorage.getItem('token'),
          token: localStorage.getItem('token'),
          userId: localStorage.getItem('userId'),
          userName: localStorage.getItem('userName'),
          userEmail: localStorage.getItem('userEmail')
        };
    
        
      
        // Only send message if auth state has changed
        if (JSON.stringify(authData) !== JSON.stringify(lastAuthState) && 
            ((!localStorage.getItem('token') && !localStorage.getItem('userEmail')) || 
             (localStorage.getItem('token') && localStorage.getItem('userEmail')))) {
          
          await chrome.storage.local.set({
            token: authData.token,
            userId: authData.userId,
            userName: authData.userName,
            userEmail: authData.userEmail
          });
      
          lastAuthState = authData;
          chrome.runtime.sendMessage({
            type: 'AUTH_CHANGED',
            data: authData
          });
        }
      
        return authData;
      }

      static async validateCredits(state) {
        try {
          const storage = await chrome.storage.local.get(['userId', 'token']);
          const userId = storage.userId;
          const token = storage.token;
      
          if (!userId || !token) {
            throw new Error('User authentication required');
          }
      
          // Get feature credits first
          const creditsResponse = await fetch('https://thinkvelocity.in/api/api/credit/credits', {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          const creditsData = await creditsResponse.json();
      
          // Calculate total required credits
          let totalRequiredCredits = 0;
      
          // Basic prompt credits
          const basicPromptCredit = creditsData.data.find(credit => credit.feature === 'basic_prompt');
          if (!basicPromptCredit) throw new Error('Basic prompt feature not found');
          totalRequiredCredits += basicPromptCredit.credits;
      
          // Style credits if style is selected
          if (state.styleType && state.styleType !== '') {
            const styleCredit = creditsData.data.find(credit => credit.feature === 'style_prompt');
            if (!styleCredit) throw new Error('Style feature not found');
            totalRequiredCredits += styleCredit.credits;
          }
      
          // Platform credits if platform is selected
          if (state.platform && state.platform !== '') {
            const platformCredit = creditsData.data.find(credit => credit.feature === 'platform');
            if (!platformCredit) throw new Error('Platform feature not found');
            totalRequiredCredits += platformCredit.credits;
          }
      
          // Get user's token balance
          const balanceResponse = await fetch(`https://thinkvelocity.in/api/api/token-types/${userId}`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          const balanceData = await balanceResponse.json();
          const tokensReceived = balanceData.data.token_received;
          const tokensUsed = balanceData.data.tokens_used;
          const availableTokens = tokensReceived - tokensUsed;
      
          if (availableTokens < totalRequiredCredits) {
            throw new Error('Insufficient tokens available');
          }
      
          return {
            success: true,
            requiredCredits: totalRequiredCredits,
            availableTokens: availableTokens
          };
        } catch (error) {
          // console.error('Credit validation failed:', error);
          throw error;
        }
      }

      static async deductCredits(state, creditsToDeduct) {
        const storage = await chrome.storage.local.get(['userId', 'token']);
        const userId = storage.userId;
        const token = storage.token;
      
        const balanceResponse = await fetch(`https://thinkvelocity.in/api/api/token-types/${userId}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        const balanceData = await balanceResponse.json();
        
        const updatedTokensUsed = balanceData.data.tokens_used + creditsToDeduct;
        
        await fetch(`https://thinkvelocity.in/api/api/token-types/${userId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            tokens_used: updatedTokensUsed,
            token_received: balanceData.data.token_received
          })
        });
      }
    }



