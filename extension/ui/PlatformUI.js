class PlatformUI {
    static getCustomStyles(platform) {
      const styles = {
        chatgpt: {
          wrapper: `
            display: grid !important;
            position: relative !important;
            min-height: 48px !important;
          `,
          input: `
            grid-column: 1/-1 !important;
            grid-row: 1/-1 !important;
            width: 100% !important;
            height: 100% !important;
            resize: none !important;
            padding-right: 45px !important;
          `,
          button: `
            position: absolute !important;
            bottom: 8px !important;
            right: 12px !important;
            z-index: 999999 !important;
          `
        },
        claude: {
          wrapper: `
            position: relative !important;
            display: block !important;
            width: 100% !important;
            min-height: 24px !important;
          `,
          input: `
            padding-right: 45px !important;
            min-height: inherit !important;
            overflow: hidden !important;
            resize: none !important;
          `,
          button: `
            bottom: 8px !important;
          `
        },
        gemini: {
          wrapper: `
            position: relative !important;
            width: 100% !important;
          `,
          input: `
            padding-right: 50px !important;
          `,
          button: `
            top: 1px !important;
            right: 12px !important;
            z-index: 999999 !important;
          `
        },
        discord: {
          wrapper: `
            position: relative !important;
            height: auto !important;
          `,
          input: `
            width: 100% !important;
            padding-right: 50px !important;
            white-space: pre-wrap !important;
          `,
          button: `
            top: 5px !important;
          `
        }
      };
   
      return styles[platform] || {};
    }
   
    static setupPlatformSpecific(element, platform) {
        switch(platform) {
          case 'chatgpt':
            this.setupChatGPT(element);
            break;
          case 'claude':
            this.setupClaude(element);
            break;
          case 'discord':
            this.setupDiscord(element);
            break;
        }
      }
     
      static setupChatGPT(element) {
        const resizeObserver = new ResizeObserver(() => {
          const wrapper = element.closest('.velocity-wrapper');
          if (wrapper) {
            wrapper.style.minHeight = '48px';
            wrapper.style.height = element.style.height;
          }
        });
        
        resizeObserver.observe(element);
        element.style.width = '100%';
        element.style.minHeight = '48px';
      }
     
      static setupClaude(element) {
        const resizeObserver = new ResizeObserver(() => {
          const height = element.scrollHeight;
          const wrapper = element.closest('.velocity-wrapper');
          if (wrapper) {
            wrapper.style.minHeight = `${height}px`;
            element.style.height = `${height}px`;
          }
        });
        
        resizeObserver.observe(element);
        this.setupClaudeEvents(element);
      }
     
      static setupDiscord(element) {
        element.style.cssText += `
          width: 100% !important;
          min-height: inherit !important;
          padding-right: 50px !important;
          box-sizing: border-box !important;
          white-space: pre-wrap !important;
          overflow-wrap: break-word !important;
        `;
      }
     
      static setupClaudeEvents(element) {
        element.addEventListener('input', () => {
          const event = new Event('change', { bubbles: true });
          element.dispatchEvent(event);
        });
     
        if (element.getAttribute('contenteditable') === 'true') {
          element.addEventListener('input', () => {
            const event = new KeyboardEvent('keyup', {
              bubbles: true,
              key: 'Space',
              keyCode: 32
            });
            element.dispatchEvent(event);
          });
        }
      }
     }