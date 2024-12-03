let userId= "";
let token = "";
async function checkFeatureAccess(featureId) {
  try {
    const userId = localStorage.getItem('userId');
    const response = await fetch(`http://127.0.0.1:3000/api/credit/credits/${featureId}/access`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ userId })
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error checking feature access:', error);
    throw error;
  }
}

async function recordFeatureUsage(featureId) {
  try {
    const userId = localStorage.getItem('userId');
    const response = await fetch(`http://127.0.0.1:3000/api/credit/use/${featureId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ userId })
    });

    const data = await response.json();
    if (!data.success) {
      throw new Error(data.message);
    }
    return data;
  } catch (error) {
    console.error('Error recording feature usage:', error);
    throw error;
  }
}

const style = document.createElement('style');
  style.textContent = `
    .responses-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 10px;
    }
    
    .response-container {
        transition: all 0.3s ease;
    }
    
    .response-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .copy-button {
        opacity: 0.7;
        transition: opacity 0.3s ease;
    }
    
    .copy-button:hover {
        opacity: 1;
    }

    .textarea-wrapper {
    position: relative !important;
    display: inline-block !important;
    width: 100% !important;
  }

  .extension-button {
    position: absolute !important;
    bottom: 5px !important;
    right: 5px !important;
    padding: 5px 10px !important;
    background: linear-gradient(180deg, #000000 0%, #008ACB 100%) !important;
    color: white !important;
    border: 1px solid #444444 !important;
    border-radius: 5px !important;
    cursor: pointer !important;
    z-index: 999999 !important;
    opacity: 0 !important;
    transition: opacity 0.3s ease !important;
    pointer-events: none !important;
  }

  .extension-button.enabled {
    opacity: 1 !important;
    pointer-events: auto !important;
  }

  .extension-button:hover {
    box-shadow: 0 0 10px rgba(0, 138, 203, 0.5) !important;
    transform: translateY(-1px) !important;
  }
    
    .copy-button.copied::after {
        content: 'Copied!';
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        pointer-events: none;
    }
`;

function updateHeaderUI() {
  if (!userId || !token) {
      // User is not logged in
      signupButton.innerHTML = `
          <span><img class="profileicon" src="./assets/profile.png" alt=""></span>
          Sign Up
      `;
      signupButton.classList.add('not-logged-in');
      
      // Add click event listener for login redirect
      //signupButton.addEventListener('click', navigateToLogin);
      
      // Hide credits button and logout button
      if (editButton) editButton.style.display = 'none';
    
  } else {
      // User is logged in
      // Show logout button
      
      // Remove the login redirect listener
      signupButton.classList.remove('not-logged-in');
      console.log("checking user id:"+userId);
      // Fetch and display user info
      fetch(`http://127.0.0.1:3000/api/users/profile/${userId}`, {
          method: 'GET',
          headers: {
              'Authorization': `Bearer ${token}`
          }
      })
      .then(response => response.json())
      .then(data => {
          signupButton.innerHTML = `
              <span><img class="profileicon" src="./assets/profile.png" alt=""></span>
              Hi ${data.data.user.name}!
          `;
          // Show credits button
          if (editButton) editButton.style.display = 'flex';
      })
      .catch(error => console.error('Error fetching user profile:', error));
  }
}

function getSelectedRadioValue() {
  const selectedRadio = document.querySelector('input[name="option"]:checked');
  console.log('Selected radio value:', selectedRadio?.value); // Debug log
  return selectedRadio ? selectedRadio.value : 'General'; // Provide default value
}
function showError(message) {
  console.error(message); // Keep console logging for debugging
  
  // Create error div with styling
  const errorDiv = document.createElement('div');
  errorDiv.className = 'error-message bg-black/40 rounded-2xl border border-red-500 p-4 mb-4';
  errorDiv.style.color = 'white';
  errorDiv.style.textAlign = 'center';
  
  // Create error content
  const errorContent = document.createElement('div');
  errorContent.className = 'flex items-center justify-center gap-2';
  
  // Add error icon (optional)
  const errorIcon = document.createElement('span');
  errorIcon.innerHTML = '⚠️';
  errorIcon.className = 'text-xl';
  
  // Add error text
  const errorText = document.createElement('span');
  errorText.textContent = message;
  
  // Assemble error message
  errorContent.appendChild(errorIcon);
  errorContent.appendChild(errorText);
  errorDiv.appendChild(errorContent);
  
  // Find and clear the response div
  const responseDiv = document.getElementById('response');
  if (responseDiv) {
    responseDiv.innerHTML = '';
    responseDiv.appendChild(errorDiv);
  }
  
  // Remove error message after 5 seconds
  setTimeout(() => {
    if (responseDiv && responseDiv.contains(errorDiv)) {
      errorDiv.remove();
    }
  }, 5000);

  // Adjust popup size if needed
  if (typeof adjustPopupSize === 'function') {
    adjustPopupSize();
  }
}
document.addEventListener('DOMContentLoaded', () => {
  // Check current auth state
  chrome.storage.local.get(['userId','token','isAuthenticated', 'userName', 'userEmail'], (data) => {
    if (data.userEmail) {
      // Update UI for logged in state
      document.getElementById('signupButton').textContent = `${data.userName}`;
      // Enable extension features
      console.log("enable features" + data.token);
      userId = data.userId;
      token = data.token;
      localStorage.setItem('userId',userId);
      localStorage.setItem('token',token);
      console.log("token:" + token);
      console.log("user Id:" + userId);
      updateCreditDisplay();
      updateHeaderUI();


      //enableFeatures();
    } else {
      // Show login prompt
      document.getElementById('signupButton').textContent = 'Please log in via the web app';
      // Disable extension features
      //disableFeatures();
      console.log("disable features");
    }
  });
});
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'AUTH_STATE_CHANGED') {
    // Update extension UI based on new auth state
    if (message.data.userEmail) {
      document.getElementById('signupButton').textContent = `Logged in as ${message.data.userName}`;
//      enableFeatures();
      console.log("enable features");

    } else {
      document.getElementById('signupButton').textContent = 'Please log in via the web app';
      //disableFeatures();
      console.log("disable features");

    }
  }
});

async function sendRequest() {
  let promptHistoryId = null;
  let creditsDeducted = false;
  let usageRecorded = false;

  try {
    const promptInput = document.getElementById('promptInput');
    const imageUpload = document.getElementById('imageUpload');
    const prompt = promptInput.value.trim();
    const selectedAIType = getSelectedRadioValue();
    const userId = localStorage.getItem('userId');

    showLoading('Processing request...');

    // Create and send request
    const formData = new FormData();
    const requestData = {
      prompt: prompt,
      style: getSelectedStyle(),
      AIType: selectedAIType || 'default'
    };

    formData.append('data', JSON.stringify(requestData));

 

    // Make the actual API request first
    const response = await fetch('http://127.0.0.1:2000/process', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(response.status === 500
        ? `Server error (500): ${await response.text()}`
        : `Server returned ${response.status}: ${await response.text()}`);
    }

    const data = await response.json();
    if (data.error) {
      throw new Error(data.error);
    }

    // Once we have a successful response, save to history
    try {
      const promptData = await savePromptToHistory(userId, prompt, selectedAIType);
      if (promptData.success) {
        promptHistoryId = promptData.data.history_id;
        lastSavedPromptId = promptHistoryId; // Set this for copy functionality
        console.log('Prompt saved with ID:', promptHistoryId);
      }
    } catch (historyError) {
      console.error('Error saving prompt to history:', historyError);
      // Continue execution even if history save fails
    }

    // Record features and deduct credits only after successful response
    try {
      // Basic prompt
      if (promptUsed) {
        await recordFeatureUsage('1');
        await handleCreditDeduction('basic_prompt');
      }

      // Image feature
      if (imageUpload && imageUpload.files.length > 0) {
        await recordFeatureUsage('3');
        await handleCreditDeduction('image_prompt');
      }

      // Advanced features
      if (advancedOptionsUsed && advancedOptionsSelected.size > 0) {
        await recordFeatureUsage('2');
        for (const optionId of advancedOptionsSelected) {
          await handleCreditDeduction(`advanced_prompt_${optionId}`);
        }
      }

      creditsDeducted = true;
      usageRecorded = true;

    } catch (creditError) {
      console.error('Error handling credits/usage:', creditError);
      // If credit deduction fails, we should still show the response
      // but log the error and notify the user
      showError('Warning: Error processing credits. Please contact support.');
    }

    // Finally, handle the response
    if (data.response) {
      handleParsedResponse(data.response);
    } else {
      throw new Error('No response data received from server');
    }

  } catch (error) {
    console.error('Request failed:', error);
    
    // Clean up any partial operations if needed
    if (promptHistoryId && (!creditsDeducted || !usageRecorded)) {
      try {
        // Add cleanup code here if needed
        console.log('Cleaning up partial operations...');
      } catch (cleanupError) {
        console.error('Error during cleanup:', cleanupError);
      }
    }

    // Show appropriate error message
    if (error.message.includes('Failed to fetch')) {
      showError('Unable to connect to server. Please make sure the backend is running.');
    } else {
      showError(`Error: ${error.message}`);
    }
  } finally {
    // Always reset the interface
    document.getElementById('promptInput').disabled = false;
    resetInterface();
  }
}
const oldHandler = document.onclick;
document.onclick = null;




function showLoading(message) {
  const responseDiv = document.getElementById('response');
  if (responseDiv) {
    responseDiv.innerHTML = `
      <div class="loading-message">
        ${message}
        <div class="loading-spinner"></div>
      </div>
    `;
    adjustPopupSize();
  }
}
function adjustPopupSize() {
  const popupHeight = document.body.scrollHeight;
  const popupWidth = document.body.scrollWidth;

  // Check if we're in a Chrome extension context
  if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
    chrome.runtime.sendMessage({
      action: 'adjustSize',
      height: popupHeight,
      width: popupWidth
    }).catch(error => {
      console.log('Size adjustment not available:', error);
    });
  }

  // Fallback: Set size directly if possible
  document.documentElement.style.width = `${popupWidth}px`;
  document.documentElement.style.height = `${popupHeight}px`;
}
// function closeAllDropdowns() {
//   document.querySelectorAll('.dropdown-content').forEach(content => {
//       content.style.display = 'none';
//   });
// }

async function savePromptToHistory(userId, promptText, aiType) {
  try {
      const response = await fetch('http://127.0.0.1:3000/api/history/prompts', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
              user_id: userId,
              prompt_text: promptText,
              ai_type: aiType,
              tokens_used: 0  // Will be updated after generation
          })
      });

      const data = await response.json();
      if (!data.success) {
          console.error('Failed to save prompt:', data.message);
          throw new Error(data.message);
      }

      return data;
  } catch (error) {
      console.error('Error saving prompt to history:', error);
      throw error;
  }
}
async function updatePromptTokens(promptId, tokensUsed) {
  try {
      const response = await fetch(`http://127.0.0.1:3000/api/history/prompts/${promptId}`, {
          method: 'PATCH',
          headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
              tokens_used: tokensUsed
          })
      });

      const data = await response.json();
      if (!data.success) {
          console.error('Failed to update tokens:', data.message);
          throw new Error(data.message);
      }

      return data;
  } catch (error) {
      console.error('Error updating prompt tokens:', error);
      throw error;
  }
}

function getSelectedCategories() {
  const selectedCategories = {};
  document.querySelectorAll('.category-card').forEach(card => {
    const categoryName = card.querySelector('.category-title').textContent;
    const selectedItem = card.querySelector('.dropdown-card.selected');
    if (selectedItem) {
      selectedCategories[categoryName] = selectedItem.querySelector('.dropdown-card-select').textContent.trim();
    }
  });
  return selectedCategories;
}
function getSelectedStyle() {
  const selectedStyle = document.querySelector('.button-group input[type="radio"]:checked');
  return selectedStyle ? selectedStyle.id : 'professional'; // Default to professional if none selected
}


function handleParsedResponse(parsedResponse) {
  const responseDiv = document.getElementById('response');
  if (!responseDiv) {
    console.error('Response div not found');
    return;
  }

  responseDiv.innerHTML = '';  // Clear previous responses

  try {
    let prompts;
    // Handle different response formats
    if (typeof parsedResponse === 'string') {
      try {
        prompts = JSON.parse(parsedResponse).prompts;
      } catch (e) {
        // If it's not JSON, treat it as a single response
        prompts = [{ prompt: parsedResponse }];
      }
    } else if (parsedResponse.prompts) {
      prompts = parsedResponse.prompts;
    } else if (Array.isArray(parsedResponse)) {
      prompts = parsedResponse;
    } else {
      prompts = [{ prompt: String(parsedResponse) }];
    }

    // Create container for responses
    const responsesContainer = document.createElement('div');
    responsesContainer.className = 'responses-container';

    // Create and append each prompt response
    prompts.forEach((promptObj, index) => {
      const container = document.createElement('div');
      container.className = 'response-container bg-black/40 rounded-2xl border border-[#444444] p-4 mb-4';

      const responseBox = document.createElement('div');
      responseBox.className = 'response-box flex justify-between items-center';

      const responseText = document.createElement('p');
      responseText.className = 'response-text text-white flex-1 mr-4';
      responseText.textContent = typeof promptObj === 'string' ? promptObj : promptObj.prompt;

      // Create copy button
      const copyButton = document.createElement('button');
      copyButton.className = 'copy-button flex items-center justify-center';
      copyButton.innerHTML = `
            <img src="./assets/copy 1.png" 
                 alt="Copy" 
                 class="w-6 h-6 cursor-pointer"
                 title="Copy to clipboard">
        `;

      // Add copy functionality
      copyButton.addEventListener('click', async () => {
        try {
            const textToCopy = typeof promptObj === 'string' ? promptObj : promptObj.prompt;
            const userId = localStorage.getItem('userId');
            const selectedAIType = getSelectedRadioValue();
            
            console.log('Copy request data:', {
                user_id: userId,
                prompt_text: textToCopy,
                original_prompt_id: lastSavedPromptId,
                ai_type: selectedAIType,
                tokens_used: lastTokensUsed
            });

            // First copy to clipboard
            await navigator.clipboard.writeText(textToCopy);

            // Validate we have all required data before making the request
            if (!userId || !lastSavedPromptId || !selectedAIType) {
                console.error('Missing required data for saving copied response:', {
                    userId,
                    lastSavedPromptId,
                    selectedAIType
                });
                throw new Error('Missing required data for saving response');
            }

            // Then save the copied response with the tokens used
            const saveResponseResponse = await fetch('http://127.0.0.1:3000/api/history/responses', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    user_id: userId,
                    prompt_text: textToCopy,
                    original_prompt_id: lastSavedPromptId,
                    ai_type: selectedAIType,
                    tokens_used: lastTokensUsed || 0
                })
            });

            const responseData = await saveResponseResponse.json();
            
            if (!responseData.success) {
                console.error('Save response error:', responseData);
                throw new Error(responseData.message || 'Failed to save response');
            }

            // Visual feedback for successful copy and save
            copyButton.classList.add('copied');
            setTimeout(() => {
                copyButton.classList.remove('copied');
            }, 2000);

            console.log('Successfully saved copied response:', responseData);

        } catch (error) {
            console.error('Failed to handle copy operation:', error);
            showError(`Failed to copy: ${error.message}`);
        }
    });

      // Assemble the response
      responseBox.appendChild(responseText);
      responseBox.appendChild(copyButton);
      container.appendChild(responseBox);
      responsesContainer.appendChild(container);
    });

    responseDiv.appendChild(responsesContainer);

  } catch (error) {
    console.error('Error handling response:', error);
    showError('Error: Could not process the response from the server.');
  }

  // Add necessary styles
  const style = document.createElement('style');
  style.textContent = `
    .responses-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 10px;
    }
    
    .response-container {
        transition: all 0.3s ease;
    }
    
    .response-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .copy-button {
        opacity: 0.7;
        transition: opacity 0.3s ease;
    }
    
    .copy-button:hover {
        opacity: 1;
    }
    
    .copy-button.copied::after {
        content: 'Copied!';
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        pointer-events: none;
    }
`;
  document.head.appendChild(style);

  // Adjust popup size after adding content
  if (typeof adjustPopupSize === 'function') {
    adjustPopupSize();
  }
}
function toggleEnhanceButton(enabled) {
  chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, {
      action: 'toggleEnhanceButton',
      enabled: enabled
    });
  });
}


// In popup.js
function updateTabsWithState(isEnabled) {
  chrome.tabs.query({}, (tabs) => {
    tabs.forEach(tab => {
      // First try to inject the content script if it's not already there
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content-script.js']
      }).then(() => {
        // After ensuring the content script is there, send the message
        return chrome.tabs.sendMessage(tab.id, {
          action: 'toggleEnhanceButton',
          enabled: isEnabled
        });
      }).catch(err => {
        console.log(`Could not update tab ${tab.id}:`, err);
      });
    });
  });
}
function initializeEnhanceToggle() {
  const toggle = document.getElementById('enhanceToggle');
  if (!toggle) {
    console.error('Toggle element not found');
    return;
  }

  // Load saved state
  chrome.storage.local.get(['enhanceButtonEnabled'], (result) => {
    const isEnabled = result.enhanceButtonEnabled === true;
    toggle.checked = isEnabled;
    
    // Notify background script to update tabs
    chrome.runtime.sendMessage({
      action: 'updateTabs',
      enabled: isEnabled
    });
  });

  // Handle toggle changes
  toggle.addEventListener('change', async (event) => {
    const isEnabled = event.target.checked;
    
    try {
      // Save state
      await chrome.storage.local.set({ 'enhanceButtonEnabled': isEnabled });
      updateActiveTab();
      // Notify background script to update tabs
      chrome.runtime.sendMessage({
        action: 'updateTabs',
        enabled: isEnabled
      });
      
    } catch (error) {
      console.error('Error handling toggle:', error);
      toggle.checked = !isEnabled; // Revert the toggle if there's an error
    }
  });
}

document.addEventListener('DOMContentLoaded', initializeEnhanceToggle);
function cleanupEventListeners() {
  const existingHandlers = [window.existingClickHandler];
  existingHandlers.forEach(handler => {
    if (handler) {
      document.removeEventListener('click', handler);
    }
  });
}

function updateActiveTab(isEnabled) {
  console.log(":called");
  chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
    const activeTab = tabs[0];
    console.log("active tab:"+activeTab.id);
    if (!activeTab) return;
    
    // Skip chrome:// URLs and other restricted pages
    // if (activeTab.url.startsWith('chrome://') || 
    //     activeTab.url.startsWith('brave://') || 
    //     activeTab.url.startsWith('chrome-extension://')) {
    //   console.log('Skipping restricted URL:', activeTab.url);
    //   return;
    // }

    try {
      console.log("helooooo");
      // Inject the content script first
      await chrome.scripting.executeScript({
        target: { tabId: activeTab.id },
        files: ['content-script.js']
      });
      console.log("reached here");
      // Then send the toggle message
      await chrome.tabs.sendMessage(activeTab.id, {
        action: 'toggleEnhanceButton',
        enabled: isEnabled
      });

    } catch (error) {
      console.log('Could not update tab:', error.message);
    }
  });
}
function updateAllTabs(isEnabled) {
  chrome.tabs.query({}, (tabs) => {
    tabs.forEach(tab => {
      chrome.tabs.sendMessage(tab.id, {
        action: 'toggleEnhanceButton',
        enabled: isEnabled
      }).catch(err => {
        console.log(`Could not send message to tab ${tab.id}:`, err);
      });
    });
  });
}
function addButtonToTextAreas() {
  const textAreas = document.querySelectorAll('textarea');
  textAreas.forEach(textArea => {
    // Skip if button already exists
    if (textArea.nextElementSibling?.classList.contains('extension-button')) {
      return;
    }

    // Create wrapper if it doesn't exist
    let wrapper = textArea.closest('.textarea-wrapper');
    if (!wrapper) {
      wrapper = document.createElement('div');
      wrapper.className = 'textarea-wrapper';
      textArea.parentNode.insertBefore(wrapper, textArea);
      wrapper.appendChild(textArea);
    }

    // Create enhance button
    const button = document.createElement('button');
    button.textContent = 'Enhance';
    button.className = 'extension-button';
    
    // Check initial state
    chrome.storage.local.get(['enhanceButtonEnabled'], (result) => {
      if (result.enhanceButtonEnabled !== false) {
        button.classList.add('enabled');
      }
    });
    
    wrapper.appendChild(button);
  });
}

document.removeEventListener('click', window.existingClickHandler);

const API_BASE_URL = 'http://127.0.0.1:5000';
document.addEventListener('DOMContentLoaded', function () {
  const sendButton = document.getElementById('sendButton');
  const promptInput = document.getElementById('promptInput');
  //const categoriesContainer = document.getElementById('categories-container');
  const responseDiv = document.getElementById('response');
  //const advancedOptionsButton = document.getElementById('advancedOptionsButton');
  const imageUpload = document.getElementById('imageUpload');
  const imageUploadText = document.querySelector('.image-upload-text');
  
  const iconImage = document.getElementById('generateIcon');
  //const logoutButton = document.querySelector('button[onclick="logout()"]');

  
  // Placeholder image path
  const placeholderImagePath = 'path/to/your/placeholder-image.png';

  const radioGroup = document.querySelector('.radio-group');

  //categoriesContainer.classList.add('hidden2');

 

  // Set up resize observer for dynamic content
  const resizeObserver = new ResizeObserver(() => {
    requestAnimationFrame(adjustPopupSize);
  });

  // Observe body for size changes
  resizeObserver.observe(document.body);

  // Event Listeners
//   if (advancedOptionsButton && categoriesContainer) {
//     // Remove any existing listeners first
//     advancedOptionsButton.replaceWith(advancedOptionsButton.cloneNode(true));
    
//     // Get the fresh reference
//     const newAdvancedOptionsButton = document.getElementById('advancedOptionsButton');
    
//     // Add the click listener
//     newAdvancedOptionsButton.addEventListener('click', function() {
//         // Toggle the hidden2 class
//         categoriesContainer.classList.toggle('hidden2');
        
//         // Log the current state
//         const isHidden = categoriesContainer.classList.contains('hidden2');
//         console.log('Advanced options panel toggled:', !isHidden);
        
//         // Make sure your hidden2 class is properly defined in CSS
//         if (!isHidden) {
//             categoriesContainer.style.display = 'grid'; // or 'block' depending on your layout
//         } else {
//             categoriesContainer.style.display = 'none';
//         }
        
//         // Adjust popup size after toggle
//         setTimeout(adjustPopupSize, 100);
//     });
// } else {
//     console.error('Advanced options elements not found:', {
//         button: !!advancedOptionsButton,
//         container: !!categoriesContainer
//     });
//   }
//   const style = document.createElement('style');
//   style.textContent = `
//      .hidden2 {
//     display: none !important;
// }

// #categories-container {
//     display: grid;
//     grid-template-columns: repeat(2, 1fr);
//     gap: 15px;
//     padding: 15px;
//     transition: all 0.3s ease;
//     opacity: 1;
//     transform: translateY(0);
// }

// #categories-container.hidden2 {
//     display: none !important;
//     opacity: 0;
//     transform: translateY(-10px);
// }

// #advancedOptionsButton {
//     cursor: pointer;
//     transition: all 0.3s ease;
// }

// #advancedOptionsButton:hover {
//     opacity: 0.8;
// }

// .category-card {
//     opacity: 1;
//     transform: translateY(0);
//     transition: all 0.3s ease;
// }

// .hidden2 .category-card {
//     opacity: 0;
//     transform: translateY(-10px);
// }

//   `;
//   document.head.appendChild(style);


//   fetch('http://localhost:2000/get_categories')
//     .then(response => response.json())
//     .then(categories => {
//       console.log('Categories:', categories);
//       categories.forEach(category => {
//         const categoryCard = createCategoryCard(category);
//         categoriesContainer.appendChild(categoryCard);
//       });
//     })
//     .catch(error => {
//       console.error('Error fetching categories:', error);
//       categoriesContainer.textContent = `Failed to load categories. Error: ${error.message}`;
//     });

//   imageUpload.addEventListener('change', function (event) {
//     const fileName = event.target.files[0]?.name;
//     imageUploadText.textContent = fileName || 'Upload Image';
//   });

//  // sendButton.addEventListener('click', sendRequest);
//   //iconImage.addEventListener('click', sendRequest);  // Add this line to make the icon work as a generate button

//   document.addEventListener('click', closeAllDropdowns);

//   new MutationObserver(adjustPopupSize).observe(document.body, { childList: true, subtree: true });
//   adjustPopupSize();

//   // Radio group initialization
//   function initializeRadioGroup() {
//     if (radioGroup) {
//       radioGroup.addEventListener('click', function (event) {
//         if (event.target.classList.contains('radio-button')) {
//           radioGroup.querySelectorAll('.radio-button').forEach(btn =>
//             btn.classList.remove('selected')
//           );
//           event.target.classList.add('selected');
//         }
//       });
//     }
//   }

//   initializeRadioGroup();

//   function createCategoryCard(category) {
//     const categoryCard = document.createElement('div');
//     categoryCard.className = 'category-card';
    
//     const categoryTitle = document.createElement('div');
//     categoryTitle.className = 'category-title';
//     categoryTitle.textContent = category.name;
//     categoryCard.appendChild(categoryTitle);

//     // Create container for dropdowns
//     const dropdownsContainer = document.createElement('div');
//     dropdownsContainer.className = 'dropdowns-container flex gap-4';

//     // Create both dropdowns
//     category.dropdowns.forEach(dropdown => {
//         const dropdownContainer = createDropdown(dropdown);
//         dropdownsContainer.appendChild(dropdownContainer);
//     });

//     categoryCard.appendChild(dropdownsContainer);
//     return categoryCard;
// }



//   function updateDropdownButton(dropdownButton, selectedItem) {
//     const nameContainer = dropdownButton.querySelector('span');
//     nameContainer.textContent = selectedItem.querySelector('.dropdown-card-select').textContent;
//   }

//   function createDropdown(dropdown) {
//     const dropdownContainer = document.createElement('div');
//     dropdownContainer.className = 'dropdown flex-1';
//     dropdownContainer.setAttribute('data-default-text', dropdown.name);

//     const dropdownButton = document.createElement('button');
//     dropdownButton.className = 'dropdown-button';
//     dropdownButton.innerHTML = `
//         <div class="dropdown-button-content">
//             <span>${dropdown.name}</span>
//         </div>
//     `;

//     const dropdownContent = document.createElement('div');
//     dropdownContent.className = 'dropdown-content';
//     dropdownContent.style.display = 'none';

//     const horizontalContainer = document.createElement('div');
//     horizontalContainer.className = 'dropdown-horizontal-container';

//     dropdown.items.forEach(item => {
//         const card = document.createElement('div');
//         card.className = 'dropdown-card';
        
//         const button = document.createElement('button');
//         button.className = 'dropdown-card-select';
//         button.textContent = item.name;
        
//         card.appendChild(button);
//         horizontalContainer.appendChild(card);
//     });

//     dropdownContent.appendChild(horizontalContainer);
//     dropdownContainer.appendChild(dropdownButton);
//     dropdownContainer.appendChild(dropdownContent);

//     dropdownButton.addEventListener('click', function(e) {
//         e.stopPropagation();
//         const isVisible = dropdownContent.style.display === 'block';
//         closeAllDropdowns();
//         dropdownContent.style.display = isVisible ? 'none' : 'block';
//     });

//     return dropdownContainer;
// }






function getSelectedValues() {
  const selected = {};
  document.querySelectorAll('.category-card').forEach(card => {
      const categoryName = card.querySelector('.category-title').textContent;
      const selectedItems = Array.from(card.querySelectorAll('.dropdown-card.selected'))
          .map(card => card.textContent.trim());
      if (selectedItems.length > 0) {
          selected[categoryName] = selectedItems;
      }
  });
  return selected;
}
// document.addEventListener('click', function(e) {
//   if (!e.target.closest('.dropdown')) {
//       closeAllDropdowns();
//   }
// });

  function adjustDropdownWidth(dropdownContent) {
    if (!dropdownContent) return;
    const buttons = dropdownContent.querySelectorAll('button');
    const maxWidth = Math.max(...Array.from(buttons).map(button => button.offsetWidth));
    dropdownContent.style.width = `${maxWidth + 103}px`;
  }

  function adjustDropdownHeight(dropdownContent) {
    if (!dropdownContent) return;
    const cards = dropdownContent.querySelectorAll('.dropdown-card');
    if (cards.length > 0) {
      const cardHeight = cards[0].offsetHeight;
      dropdownContent.style.height = `${cardHeight + 20}px`;
    }
  }

  

  
  
  //   // Updated fetch for categories
  // function fetchCategories() {
  //   return fetch(`${API_BASE_URL}/get_categories`, {
  //     method: 'GET',
  //     headers: {
  //       'Accept': 'application/json',
  //     },
  //   })
  //   .then(response => {
  //     if (!response.ok) {
  //       throw new Error(`HTTP error! status: ${response.status}`);
  //     }
  //     return response.json();
  //   })
  //   .catch(error => {
  //     console.error('Error fetching categories:', error);
  //     // Show user-friendly error message
  //     const errorMessage = error.message === 'Failed to fetch' 
  //       ? 'Unable to connect to server. Please make sure the backend is running.'
  //       : `Error: ${error.message}`;
  //     throw new Error(errorMessage);
  //   });
  // }

  // Add this function at the appropriate scope level (same level as sendRequest)
  

  // Helper function to show errors
  

  // Updated sendRequest function
  


  // Helper functions

  
});



// dropdown
document.addEventListener('DOMContentLoaded', function () {
  const signupButton = document.getElementById('signupButton');
  const dropdownMenu = document.getElementById('dropdownMenu');
  const editButton = document.getElementById('editButton');
  //const logoutButton = document.getElementById('logoutButton');
  const editDropdownMenu = document.getElementById('editDropdownMenu');
  const accountButton = document.getElementById('accountButton');
  const editDeleteButtons = document.getElementById('editDeleteButtons');
  function navigateToLogin() {
    window.location.replace('login.html');
}



// if (logoutButton) {
//   logoutButton.addEventListener('click', function(e) {
//       e.preventDefault();
//       try {
//           localStorage.clear();
//           sessionStorage.clear();
          
//           // Clear cookies
//           document.cookie.split(";").forEach(function(c) {
//               document.cookie = c.replace(/^ +/, "")
//                   .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
//           });
          
//           window.location.replace('login.html');
//       } catch (error) {
//           console.error('Logout failed:', error);
//           showError('Logout failed. Please try again.');
//       }
//   });
// }


  // Initially hide the dropdowns
  // dropdownMenu.style.display = 'none';
  // editDropdownMenu.style.display = 'none';
  // editDeleteButtons.style.display = 'none';

  // // Toggle Sign Up dropdown
  // // signupButton.addEventListener('click', function (e) {
  // //   if(userId && token){
  // //   e.stopPropagation();
  // //   dropdownMenu.style.display = dropdownMenu.style.display === 'none' ? 'block' : 'none';
  // //   editDropdownMenu.style.display = 'none'; // Hide Edit dropdown when Sign Up is clicked
  // //   }
  // // });

  // // Toggle Edit dropdown
  // editButton.addEventListener('click', function (e) {
  //   e.stopPropagation();
  //   editDropdownMenu.style.display = editDropdownMenu.style.display === 'none' ? 'block' : 'none';
  //   dropdownMenu.style.display = 'none'; // Hide Sign Up dropdown when Edit is clicked
  // });

  // // Show Edit/Delete buttons when Account button is clicked
  // accountButton.addEventListener('click', function (e) {
  //   e.stopPropagation();
  //   signupButton.style.display = 'none'; // Hide Sign Up button
  //   editDeleteButtons.style.display = 'block'; // Show Edit/Delete buttons
  //   editDropdownMenu.style.display = 'none'; // Close the Edit dropdown if open
  // });

  // Close dropdowns when clicking outside
  document.addEventListener('click', function (e) {
    if (e.target !== signupButton && e.target !== editButton && !dropdownMenu.contains(e.target) && !editDropdownMenu.contains(e.target) && e.target !== accountButton) {
      dropdownMenu.style.display = 'none';
      editDropdownMenu.style.display = 'none'; // Hide Edit dropdown
      signupButton.style.display = 'flex'; // Show Sign Up button again
      editDeleteButtons.style.display = 'none'; // Hide Edit/Delete buttons
    }
  });

  // Close dropdowns when pressing Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      dropdownMenu.style.display = 'none';
      editDropdownMenu.style.display = 'none'; // Hide Edit dropdown
      signupButton.style.display = 'flex'; // Show Sign Up button again
      editDeleteButtons.style.display = 'none'; // Hide Edit/Delete buttons
    }
  });
  // Initial UI update
  updateHeaderUI();
});

// advancedOptionsButton?.addEventListener('click', function () {
//   categoriesContainer.classList.toggle('hidden2');
//   setTimeout(adjustPopupSize, 100);
// });

function areAdvancedOptionsSelected() {
  return advancedOptionsSelected.size > 0;
}

// Assuming the user ID is available, otherwise you can retrieve it from localStorage, cookies, etc.
let lastSavedPromptId = null;
let lastTokensUsed = 0; // To track tokens used in the last operation
// const userId = 'user123'; // Replace with the actual user ID (from session, localStorage, etc.)

// Fetch User Profile data
// console.log("checking user id:"+userId);
// fetch(`http://127.0.0.1:3000/api/users/profile/${userId}`, {
//   method: 'GET',
//   headers: {
//     'Authorization': `Bearer ${token}` // Add the Authorization header with the token
//   }
// })
//   .then(response => response.json())
//   .then(data => {
//     // Assuming the API response has a 'name' field for the user's name
//     const userName = data.data.user.name;
//     console.log("data:" + data.data.user.name);
//     // Update the "Hii Nikhil" button with the user's name
//     document.getElementById('signupButton').textContent = `Hii ${userName}`; 
//     // signupButton
//     // document.getElementById('signupButton').textContent = ` ${userName}`;
//   })
//   .catch(error => console.error('Error fetching user profile:', error));

// Function to fetch and update credit display
async function updateCreditDisplay() {
  console.log("checkng user id:"+userId + `http://127.0.0.1:3000/api/token-types/${userId}`);
  console.log("checkng token:"+token);

  try {
    const response = await fetch(`http://127.0.0.1:3000/api/token-types/${userId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      }
    });
    const data = await response.json();
    console.log("data:"+data.data.token_received);
    const tokensReceived = data.data.token_received;
    const tokensUsed = data.data.tokens_used;
    document.getElementById('editButton').textContent = `${tokensReceived - tokensUsed} Credits`;
  } catch (error) {
    console.error('Error updating credit display:', error);
  }
}
  



// This is the function that will be triggered when the "Generate" button is clicked
function handleCreditDeduction(feature) {
  return new Promise((resolve, reject) => {
      fetch('http://127.0.0.1:3000/api/credit/credits', {
          method: 'GET',
          headers: {
              'Authorization': `Bearer ${token}`
          }
      })
      .then(response => response.json())
      .then(data => {
          const featureCredit = data.data.find(credit => credit.feature === feature);
          if (!featureCredit) {
              reject('Feature not found');
              return;
          }

          fetch(`http://127.0.0.1:3000/api/token-types/${userId}`, {
              method: 'GET',
              headers: {
                  'Authorization': `Bearer ${token}`,
              }
          })
          .then(response => response.json())
          .then(data => {
              const tokensReceived = data.data.token_received;
              const tokensUsed = data.data.tokens_used;

              if (tokensReceived <= tokensUsed) {
                  reject('Out of tokens');
                  return;
              }

              if (tokensReceived - tokensUsed >= featureCredit.credits) {
                  const updatedTokensUsed = tokensUsed + featureCredit.credits;
                  lastTokensUsed = featureCredit.credits; // Track tokens used

                  fetch(`http://127.0.0.1:3000/api/token-types/${userId}`, {
                      method: 'PUT',
                      headers: {
                          'Content-Type': 'application/json',
                          'Authorization': `Bearer ${token}`,
                      },
                      body: JSON.stringify({
                          tokens_used: updatedTokensUsed,
                          token_received: tokensReceived
                      })
                  })
                  .then(updateResponse => updateResponse.json())
                  .then(async (updateData) => {
                      await updateCreditDisplay();
                      resolve(featureCredit.credits);
                  })
                  .catch(error => reject(error));
              } else {
                  reject('Not enough tokens');
              }
          });
      })
      .catch(error => reject(error));
  });
}

// Feature usage tracking
let promptUsed = false;
let advancedOptionsUsed = false;
let imageGuidanceUsed = false;
const advancedOptionsSelected = new Set();

function initializeAdvancedOptions() {
  // Wait for elements to be available
  const observer = new MutationObserver((mutations, obs) => {
      const advancedOptionButtons = document.querySelectorAll('.dropdown-card');
      if (advancedOptionButtons.length) {
          obs.disconnect(); // Stop observing once elements are found
          setupAdvancedOptionListeners(advancedOptionButtons);
      }
  });

  // Start observing the document with the configured parameters
  observer.observe(document, {
      childList: true,
      subtree: true
  });
}

function setupAdvancedOptionListeners(buttons) {
    buttons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.stopPropagation();
            
            const selectElement = this.querySelector('.dropdown-card-select');
            if (!selectElement) return;
            
            const optionId = selectElement.innerText.trim();
            const dropdown = this.closest('.dropdown');
            
            // If this item is already selected, deselect it
            if (this.classList.contains('selected')) {
                this.classList.remove('selected');
                advancedOptionsSelected.delete(optionId);
                
                // Reset dropdown button text
                const dropdownButton = dropdown?.querySelector('.dropdown-button span');
                if (dropdownButton) {
                    const defaultText = dropdown.getAttribute('data-default-text') || 'Select Option';
                    dropdownButton.textContent = defaultText;
                }
            } else {
                // Deselect all other items in this dropdown
                const allCardsInDropdown = dropdown?.querySelectorAll('.dropdown-card');
                allCardsInDropdown?.forEach(card => {
                    const cardOptionId = card.querySelector('.dropdown-card-select')?.innerText.trim();
                    if (cardOptionId) {
                        advancedOptionsSelected.delete(cardOptionId);
                    }
                    card.classList.remove('selected');
                });
                
                // Select this item
                this.classList.add('selected');
                advancedOptionsSelected.add(optionId);
                
                // Update dropdown button text
                const dropdownButton = dropdown?.querySelector('.dropdown-button span');
                if (dropdownButton) {
                    dropdownButton.textContent = optionId;
                }
            }

            // Update usage flag
            advancedOptionsUsed = advancedOptionsSelected.size > 0;

            // Debug logging
            console.log('Current advanced options:', Array.from(advancedOptionsSelected));
            console.log('Advanced options used:', advancedOptionsUsed);
            
            // Update UI
            //updateAdvancedOptionsUI();
        });
    });
}
function resetAdvancedOptions() {
  // Clear the tracking set
  advancedOptionsSelected.clear();
  advancedOptionsUsed = false;

  // Reset UI elements
  document.querySelectorAll('.dropdown-card').forEach(card => {
      card.classList.remove('selected');
  });

  // Reset dropdown button texts to their defaults
  document.querySelectorAll('.dropdown').forEach(dropdown => {
      const defaultText = dropdown.getAttribute('data-default-text') || 'Select Option';
      const buttonSpan = dropdown.querySelector('.dropdown-button span');
      if (buttonSpan) {
          buttonSpan.textContent = defaultText;
      }
  });

  // Close all dropdowns
  //closeAllDropdowns();

  // Reset any visual indicators
  //updateAdvancedOptionsUI();
  
  console.log('Advanced options reset');
}

// function updateAdvancedOptionsUI() {
//   const advancedOptionsButton = document.getElementById('advancedOptionsButton');
//   if (advancedOptionsButton) {
//       advancedOptionsButton.classList.toggle('active', advancedOptionsUsed);
//   }
// }

function getAdvancedOptionsState() {
  return {
      used: advancedOptionsUsed,
      selectedOptions: Array.from(advancedOptionsSelected),
      count: advancedOptionsSelected.size
  };
}
document.addEventListener('DOMContentLoaded', initializeAdvancedOptions);

// Event listener for basic prompt
document.getElementById('promptInput').addEventListener('change', function () {
  promptUsed = true; // Mark basic prompt as used
});

// Event listeners for advanced option buttons
const advancedOptionButtons = document.querySelectorAll('.dropdown-card');
advancedOptionButtons.forEach(button => {
    button.addEventListener('click', function() {
    const optionId = this.querySelector('.dropdown-card-select').innerText; // Use button text as unique identifier
    console.log(`Advanced option clicked: ${optionId}`); // Log button click
    // advancedOptionsUsed = true;

    // Toggle the selected option
    if (!advancedOptionsSelected.has(optionId)) {
      // Add option to the selected set
      advancedOptionsSelected.add(optionId);
      // Mark the option as selected visually
      this.classList.add('selected');
    } else {
      // Remove option from the selected set
      advancedOptionsSelected.delete(optionId);
      // Remove the selected state visually
      this.classList.remove('selected');
    }

    // Update the flag for advanced options usage based on the size of the set
    advancedOptionsUsed = advancedOptionsSelected.size > 0;

    // Log the state of advancedOptionsUsed and the selected set
    console.log('Advanced options selected:', Array.from(advancedOptionsSelected));
    console.log('Advanced options used:', advancedOptionsUsed);

    // Debugging: Verify if the flag is correctly updated
    if (advancedOptionsUsed) {
      console.log('At least one advanced option is selected');
    } else {
      console.log('No advanced options are selected');
    }
  });
});

// Event listener for image upload
// document.getElementById('imageUpload').addEventListener('change', function () {
//   const allowedExtensions = ['jpg', 'jpeg', 'png', 'svg'];

//   if (this.files.length > 0) {
//     const file = this.files[0];
//     const fileExtension = file.name.split('.').pop().toLowerCase();

//     if (!allowedExtensions.includes(fileExtension)) {
//       alert('Only image files (jpg, jpeg, png) are allowed!');
//       this.value = ''; // Clear the file input
//       imageGuidanceUsed = false; // Reset usage tracking
//       return;
//     }

//     imageGuidanceUsed = true; // Mark image guidance as used
//   } else {
//     imageGuidanceUsed = false; // Reset if no files are selected
//   }
// });

// Event listener for generate button
document.getElementById('sendButton').addEventListener('click', async function () {
  if (!userId || !token) {
    showError("Please login to continue");
    return;
  }

  try {
    document.getElementById('promptInput').disabled = true;
    
    const promptInput = document.getElementById('promptInput');
    if (!promptInput || !promptInput.value.trim()) {
      showError('Please enter a prompt text');
      return;
    }

    const imageUpload = document.getElementById('imageUpload');
    const hasImage = imageUpload && imageUpload.files.length > 0;

    // First verify access to all required features
    const canProceed = await verifyAndRecordFeatures(hasImage);
    if (!canProceed) {
      return;
    }

    // If verification passed, proceed with the request
    await sendRequest();

  } catch (error) {
    console.error('Error during processing:', error);
    showError(`Error: ${error.message}`);
  } finally {
    resetInterface();
  }
});

async function verifyAndRecordFeatures(hasImage) {
  try {
    // Get current token balance first
    const tokenResponse = await fetch(`http://127.0.0.1:3000/api/token-types/${userId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      }
    });
    const tokenData = await tokenResponse.json();
    const availableTokens = tokenData.data.token_received - tokenData.data.tokens_used;

    // Get feature costs
    const creditsResponse = await fetch('http://127.0.0.1:3000/api/credit/credits', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    const creditsData = await creditsResponse.json();
    
    // Calculate total required tokens
    let requiredTokens = 0;
    if (promptUsed) {
      const basicFeature = creditsData.data.find(credit => credit.feature === 'basic_prompt');
      requiredTokens += basicFeature?.credits || 0;
    }
    if (hasImage) {
      const imageFeature = creditsData.data.find(credit => credit.feature === 'image_prompt');
      requiredTokens += imageFeature?.credits || 0;
    }
    if (advancedOptionsUsed && advancedOptionsSelected.size > 0) {
      [...advancedOptionsSelected].forEach(option => {
        const advancedFeature = creditsData.data.find(credit => credit.feature === `advanced_prompt_${option}`);
        requiredTokens += advancedFeature?.credits || 0;
      });
    }

    // Check if enough tokens are available
    if (availableTokens < requiredTokens) {
      showError('Not enough tokens available. Please top up your credits.');
      return false;
    }

    // Proceed with feature access checks
    if (promptUsed) {
      const basicAccess = await checkFeatureAccess('1');
      if (!basicAccess.data.canUse) {
        showError(basicAccess.data.reason === 'timeout'
          ? `Basic features locked until ${new Date(basicAccess.data.timeoutUntil).toLocaleTimeString()}`
          : `Daily limit reached for basic features (${basicAccess.data.usageCount}/${basicAccess.data.dailyLimit})`);
        return false;
      }
    }

    if (hasImage) {
      const imageAccess = await checkFeatureAccess('3');
      if (!imageAccess.data.canUse) {
        showError(imageAccess.data.reason === 'timeout'
          ? `Image features locked until ${new Date(imageAccess.data.timeoutUntil).toLocaleTimeString()}`
          : `Daily limit reached for image features (${imageAccess.data.usageCount}/${imageAccess.data.dailyLimit})`);
        return false;
      }
    }

    if (advancedOptionsUsed && advancedOptionsSelected.size > 0) {
      const advancedAccess = await checkFeatureAccess('2');
      if (!advancedAccess.data.canUse) {
        showError(advancedAccess.data.reason === 'timeout'
          ? `Advanced features locked until ${new Date(advancedAccess.data.timeoutUntil).toLocaleTimeString()}`
          : `Daily limit reached for advanced features (${advancedAccess.data.usageCount}/${advancedAccess.data.dailyLimit})`);
        return false;
      }
    }

    return true;
  } catch (error) {
    console.error('Error checking feature access:', error);
    showError("Error verifying feature access. Please try again.");
    return false;
  }
}

function resetInterface() {
  // Enable input
  resetAdvancedOptions();
    
  // Enable input
  document.getElementById('promptInput').disabled = false;
  
  // Reset flags
  promptUsed = false;
  imageGuidanceUsed = false;
  
  // Clear image upload
  const imageUpload = document.getElementById('imageUpload');
  if (imageUpload) {
      imageUpload.value = '';
      const imageUploadText = document.querySelector('.image-upload-text');
      if (imageUploadText) {
          imageUploadText.textContent = 'Image Guidance';
      }
  }
  
  // Clear prompt input
  const promptInput = document.getElementById('promptInput');
  if (promptInput) {
      promptInput.value = '';
  }
  
  // Update credits display
  updateCreditDisplay();

}



// Initial credit display update when page loads
updateCreditDisplay();

// Helper function to get selected advanced options count
function getSelectedAdvancedOptionsCount() {
  return advancedOptionsSelected.size;
}

    // Define logout function
    function logout() {
      try {
        // Clear all stored data
        localStorage.clear();
        sessionStorage.clear();

        // Clear cookies
        document.cookie.split(";").forEach(function (c) {
          document.cookie = c.replace(/^ +/, "")
            .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
        });

        // Redirect to login page
        window.location.href = 'login.html';
      } catch (error) {
        console.error('Logout failed:', error);
        alert('Logout failed. Please try again.');
      }
    }

    // Add click event listener to logout button
    // if (logoutButton) {
    //   // Remove the inline onclick attribute
    //   logoutButton.removeAttribute('onclick');

    //   // Add event listener
    //   logoutButton.addEventListener('click', function (e) {
    //     e.preventDefault();
    //     e.stopPropagation();
    //     logout();
    //   });
    // } else {
    //   console.warn('Logout button not found in the DOM');
    // }

    // Make logout function available globally
    window.logout = logout;