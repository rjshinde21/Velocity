const PLATFORM_CONFIG = {
    chatgpt: {
      urlPattern: /^https:\/\/chatgpt\.com/,
      selectors: '.ProseMirror[contenteditable="true"][id="prompt-textarea"], textarea.resize-none.overflow-hidden.border-0.bg-transparent',
      name: 'GPT',
      customStyles: `
        .velocity-wrapper {
          display: grid !important;
          position: relative !important;
          min-height: 48px !important;
        }
    
        .velocity-wrapper textarea {
          grid-column: 1 / -1 !important;
          grid-row: 1 / -1 !important;
          width: 100% !important;
          height: 100% !important;
          resize: none !important;
          overflow-y: hidden !important;
          padding-right: 45px !important;
          margin: 0 !important;
          border: 0 !important;
          background: transparent !important;
          box-sizing: border-box !important;
        }
    
        .velocity-wrapper span.invisible {
          visibility: hidden !important;
          white-space: pre-wrap !important;
          grid-column: 1 / -1 !important;
          grid-row: 1 / -1 !important;
          padding: 0 !important;
        }
    
        /* Hide scrollbars */
        .velocity-wrapper *::-webkit-scrollbar {
          display: none !important;
          width: 0 !important;
          height: 0 !important;
        }
      `
    },
    claude: {
      urlPattern: /^https:\/\/claude\.ai/,
      selectors: '.claude-textarea, div[contenteditable="true"]',
      name: 'Claude',
      customStyles: `
      .velocity-wrapper {
        position: relative !important;
        display: block !important;
        width: 100% !important;
        min-height: 24px !important;
        background: transparent !important;
        overflow: hidden !important;
      }
      
      .velocity-wrapper textarea,
      .velocity-wrapper [contenteditable="true"] {
        padding-right: 45px !important;
        min-height: inherit !important;
        overflow: hidden !important;
        resize: none !important;
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
        background: transparent !important;
        width: 100% !important;
        box-sizing: border-box !important;
      }
    `  
    },
    gemini: {
      urlPattern: /^https:\/\/gemini\.google\.com/,
      selectors: '.ql-editor[contenteditable="true"][role="textbox"], .textarea[contenteditable="true"]',
      name: 'Gemini',
      customStyles: `
        .velocity-wrapper {
          position: relative !important;
          display: block !important;
          width: 100% !important;
        }
        
        .velocity-wrapper [role="textbox"] {
          padding-right: 50px !important;
        }
    
        .velocity-enhance-button {
          top: 1px !important; // Update this line
          right: 12px !important;
          z-index: 999999 !important;
        }
      `
    },
    discord: {
      urlPattern: /^https:\/\/(www\.)?discord\.com\/channels/,
      selectors: '.markup_f8f345.editor_a552a6.slateTextArea_e52116, [class*="slateTextArea_"][role="textbox"]',
      name: 'Midjourney',
      customStyles: `
        .velocity-wrapper {
          position: relative !important;
          display: block !important;
          width: 100% !important;
        }
        
        .velocity-wrapper [role="textbox"] {
          padding-right: 50px !important;
        }
  
        .velocity-enhance-button {
          top: 50% !important;
          right: 12px !important;
          z-index: 999999 !important;
        }
      `
    },
    gama: {
      urlPattern: /^https:\/\/(www\.)?gamma\.app/,
      selectors: 'textarea, div[contenteditable="true"]',
      name: 'Gamma'
    },
    runway: {
      urlPattern: /^https:\/\/app\.runwayml\.com/,
      selectors: '.TextEditor-module__textbox__lvV8X, [data-lexical-editor="true"]',
      name: 'Runway',
      customStyles: `
      .velocity-wrapper {
        position: relative !important;
        display: block !important;
        width: 100% !important;
        min-height: 81px !important;
        height: auto !important;
      }
  
      .velocity-wrapper .TextEditor-module__textbox__lvV8X {
        padding-right: 50px !important;
        min-height: 81px !important;
        height: auto !important;
        max-height: none !important;
        overflow-y: visible !important;
        background: transparent !important;
        position: relative !important;
      }
  
      .velocity-wrapper .TextEditor-module__textbox__lvV8X p {
        margin: 0 !important;
        padding: 0 !important;
      }
  
      .velocity-enhance-button {
        position: absolute !important;
        top: 50% !important;
        right: 12px !important;
        transform: translateY(-50%) !important;
      }
    `
    },
    thinkvelocity: {
      urlPattern: /^https:\/\/(www\.)?thinkvelocity\.in/,
      selectors: 'textarea, div[contenteditable="true"]',
      name: 'ThinkVelocity',
      isDevelopment: true
    },
    localhost: {
      urlPattern: /^http:\/\/localhost:\d+/,
      selectors: 'textarea, div[contenteditable="true"]',
      name: 'Local Development',
      isDevelopment: true
    }
  };