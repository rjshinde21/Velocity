// let lastKnownToken = null;

// // Check local storage periodically for auth changes
// setInterval(() => {
//     const currentToken = localStorage.getItem('userToken');
    
//     if (currentToken !== lastKnownToken) {
//         lastKnownToken = currentToken;
        
//         if (currentToken) {
//             // User logged in or token changed
//             const userId = localStorage.getItem('userId');
//             const userData = localStorage.getItem('userData');
            
//             chrome.runtime.sendMessage({
//                 type: 'AUTH_CHANGED',
//                 data: {
//                     token: currentToken,
//                     userId: userId,
//                     userData: userData
//                 }
//             });
//         } else {
//             // User logged out
//             chrome.runtime.sendMessage({
//                 type: 'AUTH_CHANGED',
//                 data: null
//             });
//         }
//     }
// }, 1000);  // Check every second


// // Content script (content.js)
// let isEnhanceButtonEnabled = false;
// let isInitialized = false;
// let isButtonEnabled = false;

// const buttonStyles = document.createElement('style');
// buttonStyles.textContent = `
//   .velocity-enhance-button {
//     position: absolute !important;
//     bottom: 10px !important;
//     right: 10px !important;
//     padding: 6px 12px !important;
//     background: linear-gradient(180deg, #000000 0%, #008ACB 100%) !important;
//     color: white !important;
//     border: 1px solid #444444 !important;
//     border-radius: 5px !important;
//     cursor: pointer !important;
//     z-index: 999999 !important;
//     font-size: 13px !important;
//     display: none !important;
//   }

//   .velocity-enhance-button.visible {
//     display: block !important;
//   }

//   .velocity-wrapper {
//     position: relative !important;
//     display: inline-block !important;
//     width: 100% !important;
//   }
// `;
// document.head.appendChild(buttonStyles);


// function findAndEnhanceInputs() {
//   const inputs = document.querySelectorAll(`
//     textarea,
//     div[contenteditable="true"],
//     .claude-input-area textarea,
//     #prompt-textarea,
//     [role="textbox"]
//   `);

//   inputs.forEach(input => {
//     if (!input.closest('.velocity-wrapper')) {
//       enhanceInput(input);
//     }
//   });
// }

// // Function to enhance individual input
// function enhanceInput(input) {
//   // Create wrapper
//   const wrapper = document.createElement('div');
//   wrapper.className = 'velocity-wrapper';
//   input.parentNode.insertBefore(wrapper, input);
//   wrapper.appendChild(input);

//   // Create enhance button
//   const button = document.createElement('button');
//   button.textContent = 'Enhance';
//   button.className = 'velocity-enhance-button';
//   if (isButtonEnabled) {
//     button.classList.add('visible');
//   }

//   // Add click handler
//   button.addEventListener('click', async () => {
//     const text = input.value || input.textContent;
//     if (!text) return;

//     try {
//       button.disabled = true;
//       button.textContent = 'Enhancing...';

//       const response = await fetch('http://localhost:2000/process', {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
//         body: `data=${encodeURIComponent(JSON.stringify({
//           prompt: text,
//           style: 'professional',
//           AIType: 'General'
//         }))}`
//       });

//       const data = await response.json();
//       const enhancedText = JSON.parse(data.response).prompts[0].prompt;

//       if (input.value !== undefined) {
//         input.value = enhancedText;
//       } else {
//         input.textContent = enhancedText;
//       }
//       input.dispatchEvent(new Event('input', { bubbles: true }));

//     } catch (error) {
//       console.error('Enhancement failed:', error);
//     } finally {
//       button.disabled = false;
//       button.textContent = 'Enhance';
//     }
//   });

//   wrapper.appendChild(button);
// }


// const styles = document.createElement('style');
//   styles.textContent = `
//     .velocity-enhance-button {
//       position: absolute !important;
//       bottom: 10px !important;
//       right: 10px !important;
//       padding: 6px 12px !important;
//       background: linear-gradient(180deg, #000000 0%, #008ACB 100%) !important;
//       color: white !important;
//       border: 1px solid #444444 !important;
//       border-radius: 5px !important;
//       cursor: pointer !important;
//       z-index: 999999 !important;
//       font-size: 13px !important;
//       display: none !important;
//     }

//     .velocity-enhance-button.visible {
//       display: block !important;
//     }

//     .velocity-wrapper {
//       position: relative !important;
//       display: inline-block !important;
//       width: 100% !important;
//     }
//       .velocity-button-container {
//     position: relative;
//     display: inline-block;
//   }

//   .velocity-enhance-button {
//     position: absolute !important;
//     bottom: 10px !important;
//     right: 10px !important;
//     z-index: 9999 !important;
//     padding: 6px 12px !important;
//     background: linear-gradient(180deg, #000000 0%, #008ACB 100%) !important;
//     color: white !important;
//     border: 1px solid #444444 !important;
//     border-radius: 5px !important;
//     cursor: pointer !important;
//     font-size: 13px !important;
//     font-family: system-ui, -apple-system, sans-serif !important;
//     transition: all 0.2s ease !important;
//   }

//   .velocity-enhance-button:hover {
//     box-shadow: 0 0 10px rgba(0, 138, 203, 0.5) !important;
//     transform: translateY(-1px) !important;
//   }

//   .velocity-enhance-button:disabled {
//     opacity: 0.6 !important;
//     cursor: not-allowed !important;
//     transform: none !important;
//   }

//    .textarea-wrapper {
//     position: relative !important;
//     display: inline-block !important;
//     width: 100% !important;
//   }

//   .extension-button {
//     position: absolute !important;
//     bottom: 5px !important;
//     right: 5px !important;
//     padding: 5px 10px !important;
//     background: linear-gradient(180deg, #000000 0%, #008ACB 100%) !important;
//     color: white !important;
//     border: 1px solid #444444 !important;
//     border-radius: 5px !important;
//     cursor: pointer !important;
//     z-index: 999999 !important;
//     display: none !important;
//     font-size: 12px !important;
//   }

//   .extension-button.enabled {
//     display: block !important;
//   }

//   .extension-button:hover {
//     box-shadow: 0 0 10px #008ACB !important;
//   }
//   `;
//   document.head.appendChild(styles);

// chrome.runtime.sendMessage({ action: 'contentScriptReady' });

// // Listen for messages from popup
// chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
//   if (message.action === 'toggleEnhanceButton') {
//     isButtonEnabled = message.enabled;
//     document.querySelectorAll('.velocity-enhance-button').forEach(button => {
//       if (isButtonEnabled) {
//         button.classList.add('visible');
//       } else {
//         button.classList.remove('visible');
//       }
//     });
//   }
// });

// // Initial setup
// findAndEnhanceInputs();

// const observer = new MutationObserver(() => {
//   if (isButtonEnabled) {
//     findAndEnhanceInputs();
//   }
// });

// observer.observe(document.body, {
//   childList: true,
//   subtree: true
// });

// function addEnhanceButton(input) {
//   const wrapper = document.createElement('div');
//   wrapper.className = 'velocity-wrapper';
//   input.parentNode.insertBefore(wrapper, input);
//   wrapper.appendChild(input);

//   const button = document.createElement('button');
//   button.textContent = 'Enhance';
//   button.className = 'velocity-enhance-button';
//   button.addEventListener('click', () => enhanceInput(input));
//   wrapper.appendChild(button);
// }

// function initializeEnhanceButton() {
//   // Add the styles once
  

//   // Set up the mutation observer
//   // const observer = new MutationObserver(() => {
//   //   document.querySelectorAll('textarea, div[contenteditable="true"]').forEach(input => {
//   //     if (!input.closest('.velocity-wrapper')) {
//   //       addEnhanceButton(input);
//   //     }
//   //   });
//   // });
  
//   // observer.observe(document.body, {
//   //   childList: true,
//   //   subtree: true
//   // });

//   // Initial button addition
//   addEnhanceButtons();
// }


// function updateEnhanceButtonVisibility() {
//   document.querySelectorAll('.velocity-enhance-button').forEach(button => {
//     button.style.display = isEnhanceButtonEnabled ? 'block' : 'none';
//   });
// }

// async function enhanceInput(input) {
//   const text = input.value || input.textContent;
//   if (!text) return;

//   try {
//     const response = await fetch('http://localhost:2000/process', {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify({ prompt: text, style: 'professional', AIType: 'General' })
//     });
//     const result = await response.json();
//     const enhancedText = JSON.parse(result.response).prompts[0].prompt;

//     if (input.value !== undefined) {
//       input.value = enhancedText;
//     } else {
//       input.textContent = enhancedText;
//     }
//     input.dispatchEvent(new Event('input', { bubbles: true }));
//   } catch (error) {
//     console.error('Enhancement failed:', error);
//   }
// }


// function addEnhanceButtons() {
//   const inputs = document.querySelectorAll(`
//     textarea,
//     div[contenteditable="true"],
//     .claude-input-area textarea,
//     #prompt-textarea
//   `);

//   inputs.forEach(input => {
//     if (input.closest('.velocity-wrapper')) return;

//     const wrapper = document.createElement('div');
//     wrapper.className = 'velocity-wrapper';
//     input.parentNode.insertBefore(wrapper, input);
//     wrapper.appendChild(input);

//     const button = document.createElement('button');
//     button.className = 'velocity-enhance-button';
//     button.textContent = 'Enhance';
//     button.style.display = isEnhanceButtonEnabled ? 'block' : 'none';
    
//     button.addEventListener('click', async () => {
//       const text = input.value || input.textContent;
//       if (!text) return;
      
//       try {
//         button.disabled = true;
//         button.textContent = 'Enhancing...';
        
//         const response = await fetch('http://localhost:2000/process', {
//           method: 'POST',
//           headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
//           body: `data=${encodeURIComponent(JSON.stringify({
//             prompt: text,
//             style: 'professional',
//             AIType: 'General'
//           }))}`
//         });

//         const data = await response.json();
//         const enhancedText = JSON.parse(data.response).prompts[0].prompt;
        
//         if (input.value !== undefined) {
//           input.value = enhancedText;
//         } else {
//           input.textContent = enhancedText;
//         }
//         input.dispatchEvent(new Event('input', { bubbles: true }));
        
//       } catch (error) {
//         console.error('Enhancement failed:', error);
//       } finally {
//         button.disabled = false;
//         button.textContent = 'Enhance';
//       }
//     });

//     wrapper.appendChild(button);
//   });
// }

// // const styles = document.createElement('style');
// // styles.textContent = `
// //   .velocity-button-container {
// //     position: relative;
// //     display: inline-block;
// //   }

// //   .velocity-enhance-button {
// //     position: absolute !important;
// //     bottom: 10px !important;
// //     right: 10px !important;
// //     z-index: 9999 !important;
// //     padding: 6px 12px !important;
// //     background: linear-gradient(180deg, #000000 0%, #008ACB 100%) !important;
// //     color: white !important;
// //     border: 1px solid #444444 !important;
// //     border-radius: 5px !important;
// //     cursor: pointer !important;
// //     font-size: 13px !important;
// //     font-family: system-ui, -apple-system, sans-serif !important;
// //     transition: all 0.2s ease !important;
// //   }

// //   .velocity-enhance-button:hover {
// //     box-shadow: 0 0 10px rgba(0, 138, 203, 0.5) !important;
// //     transform: translateY(-1px) !important;
// //   }

// //   .velocity-enhance-button:disabled {
// //     opacity: 0.6 !important;
// //     cursor: not-allowed !important;
// //     transform: none !important;
// //   }
// // `;
// // document.head.appendChild(styles);



// function addOrRemoveEnhanceButtons() {
//   // First, remove any existing enhance buttons
//   document.querySelectorAll('.velocity-enhance-button').forEach(button => button.remove());

//   // If not enabled, we don't need to add new buttons
//   if (!isEnhanceButtonEnabled) return;

//   // Find text inputs on common AI platforms
//   const inputs = document.querySelectorAll(`
//     textarea[data-id="root"],
//     #prompt-textarea,
//     div[contenteditable="true"],
//     .claude-input-area textarea,
//     textarea.claude-textarea
//   `);

//   inputs.forEach(input => {
//     // Create the enhance button
//     const button = document.createElement('button');
//     button.className = 'velocity-enhance-button';
//     button.textContent = 'Enhance';
    
//     // Position the button container relative to the input
//     const container = document.createElement('div');
//     container.className = 'velocity-button-container';
    
//     // Add the button to the container
//     container.appendChild(button);
    
//     // Insert the container after the input
//     input.parentNode.insertBefore(container, input.nextSibling);
    
//     // Add click handler
//     button.addEventListener('click', () => {
//       const text = input.value || input.textContent;
//       if (text) {
//         handleEnhanceClick(text, input);
//       }
//     });
//   });
// }

// async function handleEnhanceClick(text, input) {
//   try {
//     const button = input.nextSibling.querySelector('.velocity-enhance-button');
//     button.textContent = 'Enhancing...';
//     button.disabled = true;

//     const response = await fetch('http://localhost:2000/process', {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/x-www-form-urlencoded',
//       },
//       body: `data=${encodeURIComponent(JSON.stringify({
//         prompt: text,
//         style: 'professional',
//         AIType: 'General'
//       }))}`
//     });

//     const data = await response.json();
//     const enhancedText = JSON.parse(data.response).prompts[0].prompt;
    
//     if (input.value !== undefined) {
//       input.value = enhancedText;
//     } else {
//       input.textContent = enhancedText;
//     }
//     input.dispatchEvent(new Event('input', { bubbles: true }));
    
//   } catch (error) {
//     console.error('Enhancement failed:', error);
//   } finally {
//     const button = input.nextSibling.querySelector('.velocity-enhance-button');
//     button.textContent = 'Enhance';
//     button.disabled = false;
//   }
// }

// // Function to add enhance button to textareas
// function addButtonToTextAreas() {
//   const textAreas = document.querySelectorAll('textarea');
//   textAreas.forEach(textArea => {
//     // Skip if button already exists
//     if (textArea.nextElementSibling && textArea.nextElementSibling.classList.contains('extension-button')) {
//       return;
//     }

//     // Create wrapper if it doesn't exist
//     let wrapper = textArea.closest('.textarea-wrapper');
//     if (!wrapper) {
//       wrapper = document.createElement('div');
//       wrapper.className = 'textarea-wrapper';
//       textArea.parentNode.insertBefore(wrapper, textArea);
//       wrapper.appendChild(textArea);
//     }

//     // Create enhance button
//     const button = document.createElement('button');
//     button.textContent = 'Enhance';
//     button.className = `extension-button ${isEnhanceButtonEnabled ? 'enabled' : ''}`;
    
//     // Add click handler
//     button.addEventListener('click', async () => {
//       if (!isEnhanceButtonEnabled) return;

//       try {
//         // First notify the extension
//         chrome.runtime.sendMessage({
//           action: "openPopup",
//           text: textArea.value
//         });

//         // Then handle local enhancement if enabled
//         if (isEnhanceButtonEnabled) {
//           // Remove any existing popovers
//           wrapper.querySelectorAll('.enhance-popover').forEach(p => p.remove());

//           const response = await fetch('http://localhost:2000/process', {
//             method: 'POST',
//             headers: {
//               'Content-Type': 'application/x-www-form-urlencoded',
//             },
//             body: `data=${encodeURIComponent(JSON.stringify({
//               prompt: textArea.value,
//               style: 'professional', // Use the style from popup
//               AIType: 'General'
//             }))}`
//           });

//           const data = await response.json();
//           if (data.error) throw new Error(data.error);

//           // Create and show popover with enhanced text
//           const enhancedText = JSON.parse(data.response).prompts[0].prompt;
//           const popover = document.createElement('div');
//           popover.className = 'enhance-popover';
//           popover.innerHTML = `
//             <div class="enhanced-text">${enhancedText}</div>
//             <div class="enhance-actions">
//               <button class="copy-btn">Copy</button>
//               <button class="replace-btn">Replace</button>
//             </div>
//           `;

//           wrapper.appendChild(popover);

//           // Add button handlers
//           popover.querySelector('.copy-btn').onclick = async () => {
//             await navigator.clipboard.writeText(enhancedText);
//             popover.remove();
//           };

//           popover.querySelector('.replace-btn').onclick = () => {
//             textArea.value = enhancedText;
//             textArea.dispatchEvent(new Event('input', { bubbles: true }));
//             popover.remove();
//           };

//           // Close popover when clicking outside
//           document.addEventListener('click', function closePopover(e) {
//             if (!popover.contains(e.target) && e.target !== button) {
//               popover.remove();
//               document.removeEventListener('click', closePopover);
//             }
//           });
//         }
//       } catch (error) {
//         console.error('Enhancement failed:', error);
//       }
//     });

//     wrapper.appendChild(button);
//   });
// }

// if (document.readyState === 'complete') {
//   initializeEnhanceButton();
// } else {
//   window.addEventListener('load', initializeEnhanceButton);
// }

// // Function to update all enhance buttons' visibility
// function updateEnhanceButtons() {
//   console.log('Updating enhance buttons, enabled:', isEnhanceButtonEnabled); // Debug log
//   document.querySelectorAll('.extension-button').forEach(button => {
//     if (isEnhanceButtonEnabled) {
//       button.classList.add('enabled');
//     } else {
//       button.classList.remove('enabled');
//     }
//   });
// }

// // Add required styles
// // const styles = `
// //   .textarea-wrapper {
// //     position: relative !important;
// //     display: inline-block !important;
// //     width: 100% !important;
// //   }

// //   .extension-button {
// //     position: absolute !important;
// //     bottom: 5px !important;
// //     right: 5px !important;
// //     padding: 5px 10px !important;
// //     background: linear-gradient(180deg, #000000 0%, #008ACB 100%) !important;
// //     color: white !important;
// //     border: 1px solid #444444 !important;
// //     border-radius: 5px !important;
// //     cursor: pointer !important;
// //     z-index: 999999 !important;
// //     display: none !important;
// //     font-size: 12px !important;
// //   }

// //   .extension-button.enabled {
// //     display: block !important;
// //   }

// //   .extension-button:hover {
// //     box-shadow: 0 0 10px #008ACB !important;
// //   }
// // `;

// // Add styles to document
// const styleSheet = document.createElement('style');
// styleSheet.textContent = styles;
// document.head.appendChild(styleSheet);

// // Initialize
// // addButtonToTextAreas();

// // Set up observer for dynamic content
// // const observer = new MutationObserver((mutations) => {
// //   mutations.forEach((mutation) => {
// //     mutation.addedNodes.forEach((node) => {
// //       if (node.nodeName === 'TEXTAREA') {
// //         addButtonToTextAreas();
// //       }
// //       if (node.getElementsByTagName) {
// //         const textareas = node.getElementsByTagName('textarea');
// //         if (textareas.length) {
// //           addButtonToTextAreas();
// //         }
// //       }
// //     });
// //   });
// // });

// // observer.observe(document.body, {
// //   childList: true,
// //   subtree: true
// // });

// // const observer = new MutationObserver(() => {
// //   if (isEnhanceButtonEnabled) {
// //     addOrRemoveEnhanceButtons();
// //   }
// // });

// // observer.observe(document.body, {
// //   childList: true,
// //   subtree: true
// // });

// Single source of truth for state
const state = {
  isEnabled: false,
  isInitialized: false,
  selectedLLM: 'General', // Default LLM type
  enhancedPrompts: [] // Store generated prompts
};
// Single style definition
const enhanceStyles = document.createElement('style');
enhanceStyles.textContent = `
  .velocity-enhance-button {
    position: absolute !important;
    bottom: 10px !important;
    right: 10px !important;
    padding: 6px 12px !important;
    background: linear-gradient(180deg, #000000 0%, #008ACB 100%) !important;
    color: white !important;
    border: 1px solid #444444 !important;
    border-radius: 5px !important;
    cursor: pointer !important;
    z-index: 999999 !important;
    display: none !important;
  }

  .velocity-enhance-button.visible {
    display: block !important;
  }

  .velocity-wrapper {
    position: relative !important;
    display: inline-block !important;
    width: 100% !important;
  }

  .velocity-prompt-popup {
    position: absolute !important;
    bottom: calc(100% + 10px) !important;
    left: 0 !important;
    width: 300px !important;
    max-height: 400px !important;
    background: #000000 !important;
    border: 1px solid #444444 !important;
    border-radius: 8px !important;
    padding: 12px !important;
    z-index: 999999 !important;
    display: none;
    overflow-y: auto !important;
    color: white !important;
  }

  .velocity-prompt-option {
    padding: 12px !important;
    margin-bottom: 8px !important;
    background: rgba(0, 138, 203, 0.1) !important;
    border: 1px solid #444444 !important;
    border-radius: 6px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
  }

  .velocity-prompt-option:hover {
    background: rgba(0, 138, 203, 0.2) !important;
    transform: translateY(-1px) !important;
  }

  .velocity-prompt-actions {
    display: flex !important;
    gap: 8px !important;
    margin-top: 8px !important;
  }

  .velocity-prompt-button {
    flex: 1 !important;
    padding: 6px 12px !important;
    background: linear-gradient(180deg, #008ACB 0%, #006494 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 4px !important;
    cursor: pointer !important;
    font-size: 12px !important;
  }
`;
document.head.appendChild(enhanceStyles);

// Single function to handle button visibility
function updateButtonVisibility() {
  document.querySelectorAll('.velocity-enhance-button').forEach(button => {
    if (state.isEnabled) {
      button.classList.add('visible');
    } else {
      button.classList.remove('visible');
    }
  });
}

// Single function to enhance inputs
async function generateEnhancedPrompts(text) {
  try {
    const response = await fetch('http://localhost:2000/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `data=${encodeURIComponent(JSON.stringify({
        prompt: text,
        style: 'professional',
        AIType: state.selectedLLM
      }))}`
    });

    const data = await response.json();
    return JSON.parse(data.response).prompts;
  } catch (error) {
    console.error('Failed to generate prompts:', error);
    throw error;
  }
}

// Enhanced input enhancement function
function enhanceInput(input) {
  if (input.dataset.velocityEnhanced) return;
  
  const wrapper = document.createElement('div');
  wrapper.className = 'velocity-wrapper';
  input.parentNode.insertBefore(wrapper, input);
  wrapper.appendChild(input);

  const button = document.createElement('button');
  button.textContent = 'Enhance';
  button.className = 'velocity-enhance-button';
  if (state.isEnabled) {
    button.classList.add('visible');
  }

  // Create popup for enhanced prompts
  const promptPopup = document.createElement('div');
  promptPopup.className = 'velocity-prompt-popup';
  wrapper.appendChild(promptPopup);

  button.addEventListener('click', async () => {
    const text = input.value || input.textContent;
    if (!text) return;

    try {
      button.disabled = true;
      button.textContent = 'Enhancing...';
      promptPopup.style.display = 'block';

      // Show loading state
      promptPopup.innerHTML = `
        <div class="velocity-prompt-option">
          Generating enhanced prompts...
        </div>
      `;

      // Generate prompts
      const prompts = await generateEnhancedPrompts(text);
      state.enhancedPrompts = prompts;

      // Show prompts with actions
      promptPopup.innerHTML = prompts.map((prompt, index) => `
        <div class="velocity-prompt-option">
          ${prompt.prompt}
          <div class="velocity-prompt-actions">
            <button class="velocity-prompt-button" onclick="window.velocityActions.copyPrompt(${index})">
              Copy
            </button>
            <button class="velocity-prompt-button" onclick="window.velocityActions.replacePrompt(${index})">
              Replace
            </button>
          </div>
        </div>
      `).join('');

    } catch (error) {
      console.error('Enhancement failed:', error);
      promptPopup.innerHTML = `
        <div class="velocity-prompt-option">
          Failed to generate prompts. Please try again.
        </div>
      `;
    } finally {
      button.disabled = false;
      button.textContent = 'Enhance';
    }
  });

  // Add popup close handler
  document.addEventListener('click', (e) => {
    if (!promptPopup.contains(e.target) && !button.contains(e.target)) {
      promptPopup.style.display = 'none';
    }
  });

  wrapper.appendChild(button);
  input.dataset.velocityEnhanced = 'true';

  // Add global actions for the buttons
  window.velocityActions = {
    copyPrompt: (index) => {
      const prompt = state.enhancedPrompts[index].prompt;
      navigator.clipboard.writeText(prompt);
      promptPopup.style.display = 'none';
    },
    replacePrompt: (index) => {
      const prompt = state.enhancedPrompts[index].prompt;
      if (input.value !== undefined) {
        input.value = prompt;
      } else {
        input.textContent = prompt;
      }
      input.dispatchEvent(new Event('input', { bubbles: true }));
      promptPopup.style.display = 'none';
    }
  };
}

// Single function to scan for inputs
function findAndEnhanceInputs() {
  const inputs = document.querySelectorAll(`
    textarea,
    div[contenteditable="true"],
    .claude-input-area textarea,
    #prompt-textarea,
    [role="textbox"]
  `);

  inputs.forEach(input => {
    if (!input.closest('.velocity-wrapper')) {
      enhanceInput(input);
    }
  });
}

// Single observer instance
const observer = new MutationObserver(() => {
  if (state.isEnabled) {
    findAndEnhanceInputs();
  }
});

// Message handler
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'toggleEnhanceButton') {
    state.isEnabled = message.enabled;
    updateButtonVisibility();
    
    if (!state.isInitialized) {
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
      state.isInitialized = true;
    }
  } else if (message.action === 'setLLMType') {
    state.selectedLLM = message.llmType;
  }
});

// Initial setup
findAndEnhanceInputs();