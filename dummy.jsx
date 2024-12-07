document.addEventListener('DOMContentLoaded', function () {
    const sendButton = document.getElementById('sendButton');
    const promptInput = document.getElementById('promptInput');
    const categoriesContainer = document.getElementById('categories-container');
    const responseDiv = document.getElementById('response');
    const advancedOptionsButton = document.getElementById('advancedOptionsButton');
    const imageUpload = document.getElementById('imageUpload');
    const imageUploadText = document.querySelector('.image-upload-text');
    const API_BASE_URL = 'http://localhost:5000';
    const iconImage = document.getElementById('generateIcon');
    const logoutButton = document.querySelector('button[onclick="logout()"]');
  
    // Placeholder image path
    const placeholderImagePath = 'path/to/your/placeholder-image.png';
    const categoryStructure = [
      {
        name: "Craft your vision with the perfect subject and style",
        col1: 0,  // First column index for this category
        col2: 1   // Second column index for this category
      },
      {
        name: "Set the stage with your ideal background and setting",
        col1: 2,
        col2: 3
      },
      {
        name: "Illuminate your scene with the perfect lighting and colors",
        col1: 4,
        col2: 5
      },
      {
        name: "Capture the essence with the right mood and details",
        col1: 6,
        col2: 7
      }
    ];
  
    const radioGroup = document.querySelector('.radio-group');
  
    categoriesContainer.classList.add('hidden2');
  
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
  
    // Set up resize observer for dynamic content
    const resizeObserver = new ResizeObserver(() => {
      requestAnimationFrame(adjustPopupSize);
    });
  
    // Observe body for size changes
    resizeObserver.observe(document.body);
  
    // Event Listeners
    advancedOptionsButton?.addEventListener('click', function () {
      categoriesContainer.classList.toggle('hidden2');
      setTimeout(adjustPopupSize, 100); // Allow time for transition
    });
  
    fetch(`${API_BASE_URL}/get_categories`)
      .then(response => response.json())
      .then(data => {
        categoriesContainer.innerHTML = ''; // Clear existing content
        
        // Group the data into column pairs
        const columnPairs = [];
        for (let i = 0; i < data.length; i += 2) {
          columnPairs.push([
            data[i]?.items || [],
            data[i + 1]?.items || []
          ]);
        }
        
        // Create category cards
        categoryStructure.forEach((category, index) => {
          if (columnPairs[index]) {
            const card = createCategoryCard(category, columnPairs[index]);
            categoriesContainer.appendChild(card);
          }
        });
      })
      .catch(error => {
        console.error('Error fetching categories:', error);
        categoriesContainer.innerHTML = `
          <div class="text-red-500 p-4">
            Failed to load categories. Please try again later.
          </div>
        `;
      });
  
    imageUpload.addEventListener('change', function (event) {
      const fileName = event.target.files[0]?.name;
      imageUploadText.textContent = fileName || 'Upload Image';
    });
  
    sendButton.addEventListener('click', sendRequest);
    iconImage.addEventListener('click', sendRequest);  // Add this line to make the icon work as a generate button
  
    document.addEventListener('click', closeAllDropdowns);
  
    new MutationObserver(adjustPopupSize).observe(document.body, { childList: true, subtree: true });
    adjustPopupSize();
  
    // Radio group initialization
    function initializeRadioGroup() {
      if (radioGroup) {
        radioGroup.addEventListener('click', function (event) {
          if (event.target.classList.contains('radio-button')) {
            radioGroup.querySelectorAll('.radio-button').forEach(btn =>
              btn.classList.remove('selected')
            );
            event.target.classList.add('selected');
          }
        });
      }
    }
  
    initializeRadioGroup();
  
    function createCategoryCard(categoryInfo, columnData) {
      const categoryCard = document.createElement('div');
      categoryCard.className = 'category-card bg-black/40 rounded-2xl border border-[#444444] p-4 mb-4';
      
      const categoryTitle = document.createElement('div');
      categoryTitle.className = 'category-title text-white font-medium mb-3';
      categoryTitle.textContent = categoryInfo.name;
      
      const dropdownsContainer = document.createElement('div');
      dropdownsContainer.className = 'flex gap-4';
  
      // Create the two dropdowns for this category
      [categoryInfo.col1, categoryInfo.col2].forEach((colIndex) => {
        const items = columnData[colIndex] || [];
        const dropdownContainer = createDropdown(items, colIndex);
        dropdownsContainer.appendChild(dropdownContainer);
      });
  
      categoryCard.appendChild(categoryTitle);
      categoryCard.appendChild(dropdownsContainer);
  
      return categoryCard;
    }
  
  
  
    function updateDropdownButton(dropdownButton, selectedItem) {
      const nameContainer = dropdownButton.querySelector('span');
      nameContainer.textContent = selectedItem.querySelector('.dropdown-card-select').textContent;
    }
  
    function createDropdown(items, colIndex) {
      const dropdownContainer = document.createElement('div');
      dropdownContainer.className = 'dropdown flex-1';
  
      const dropdownButton = document.createElement('button');
      dropdownButton.className = 'dropdown-button w-fit bg-black/60 text-white rounded-lg p-2 flex justify-center items-center border border-[#444444] hover:bg-black/80 transition-colors';
      const selectedCategory = items[0]?.name || 'Select'; 
      console.log('selectedCategory', selectedCategory)
  
      dropdownButton.innerHTML = `
        <div class="dropdown-button-content">
          <span>${selectedCategory}</span>
        </div>
        <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
        </svg>
      `;
  
      const dropdownContent = document.createElement('div');
      dropdownContent.className = 'dropdown-content hidden absolute z-10 w-full mt-1 bg-black/95 rounded-lg border border-[#444444] max-h-48 overflow-y-auto';
  
      const itemsContainer = document.createElement('div');
      itemsContainer.className = 'p-2';
  
      items.forEach(item => {
        const option = document.createElement('div');
        option.className = 'dropdown-item p-2 text-white hover:bg-white/10 rounded cursor-pointer transition-colors';
        option.textContent = item.name; // Using the 'name' property from your CSV structure
        
        option.addEventListener('click', function() {
          const buttonText = dropdownButton.querySelector('span');
          buttonText.textContent = item.name;
          dropdownContent.classList.add('hidden');
          
          // Remove selected class from all items in this dropdown
          itemsContainer.querySelectorAll('.dropdown-item').forEach(el => {
            el.classList.remove('selected', 'bg-white/20');
          });
          
          // Add selected class to clicked item
          option.classList.add('selected', 'bg-white/20');
        });
  
        itemsContainer.appendChild(option);
      });
  
      dropdownContent.appendChild(itemsContainer);
      dropdownContainer.appendChild(dropdownButton);
      dropdownContainer.appendChild(dropdownContent);
  
      // Toggle dropdown
      dropdownButton.addEventListener('click', function(e) {
        e.stopPropagation();
        const isHidden = dropdownContent.classList.contains('hidden');
        
        // Hide all dropdowns first
        document.querySelectorAll('.dropdown-content').forEach(content => {
          content.classList.add('hidden');
        });
        
        // Toggle current dropdown
        if (isHidden) {
          dropdownContent.classList.remove('hidden');
        }
      });
  
      return dropdownContainer;
    }
  
    document.addEventListener('click', function() {
      document.querySelectorAll('.dropdown-content').forEach(content => {
        content.classList.add('hidden');
      });
    });
  
  
    function closeAllDropdowns() {
      document.querySelectorAll('.dropdown-content').forEach(content => {
        content.style.display = 'none';
      });
    }
  
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
  
    function getSelectedRadioValue() {
      const selectedRadio = radioGroup ? radioGroup.querySelector('.radio-button.selected') : null;
      return selectedRadio ? selectedRadio.textContent.trim() : null;
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
      console.log('selectedCategories', selectedCategories)
      return selectedCategories;
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
              await navigator.clipboard.writeText(textToCopy);
  
              // Visual feedback
              copyButton.classList.add('copied');
              setTimeout(() => {
                copyButton.classList.remove('copied');
              }, 2000);
            } catch (error) {
              console.error('Failed to copy text:', error);
              showError('Failed to copy text to clipboard');
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
      style.textContent = `.
      .dropdown-content {
        scrollbar-width: thin;
        scrollbar-color: #666 #333;
      }
      
      .dropdown-content::-webkit-scrollbar {
        width: 6px;
      }
      
      .dropdown-content::-webkit-scrollbar-track {
        background: #333;
        border-radius: 3px;
      }
      
      .dropdown-content::-webkit-scrollbar-thumb {
        background: #666;
        border-radius: 3px;
      }
      
      .dropdown-button:focus {
        outline: none;
        ring-2 ring-white/20;
      }
      
      .dropdown-item.selected {
        background-color: rgba(255, 255, 255, 0.2);
      }
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
  
    // Helper function to show errors
    function showError(message) {
      const responseDiv = document.getElementById('response');
      if (responseDiv) {
        responseDiv.innerHTML = `
            <div class="error-message bg-red-100 text-red-800 p-3 rounded-lg border border-red-300">
                ${message}
            </div>
        `;
      }
    }
    // Updated sendRequest function
    function sendRequest() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      // Debug logging
      console.log('Send request initiated');
  
      // Check if elements exist
      const promptInput = document.getElementById('promptInput');
      if (!promptInput) {
        showError('Error: Prompt input element not found');
        return;
      }
  
      const prompt = promptInput.value.trim();
      const selectedCategories = getSelectedCategories();
      const selectedAIType = getSelectedRadioValue();
  
      console.log('selectedCategories', selectedCategories)
  
      // Log the data being sent
      console.log('Sending data:', {
        prompt,
        selectedCategories,
        selectedAIType
      });
  
      // Validate inputs
      if (!prompt && (!imageUpload || imageUpload.files.length === 0)) {
        showError('Please enter a prompt first then upload an image.');
        return;
      }
  
      showLoading('Processing request...');
  
      const formData = new FormData();
  
      // Add data with error checking
      try {
        const requestData = {
          prompt: prompt || '',
          category: selectedCategories || {},
          AIType: selectedAIType || 'default'
        };
  
        formData.append('data', JSON.stringify(requestData));
  
        if (imageUpload && imageUpload.files.length > 0) {
          formData.append('image', imageUpload.files[0]);
        }
      } catch (error) {
        showError('Error preparing request data: ' + error.message);
        return;
      }
  
      // Send request with detailed error handling
      fetch(`${API_BASE_URL}/process`, {
        method: 'POST',
        body: formData,
      })
        .then(async response => {
          if (!response.ok) {
            // Try to get error details from response
            const errorText = await response.text();
            console.error('Server error details:', errorText);
  
            throw new Error(
              response.status === 500
                ? `Server error (500): ${errorText}`
                : `Server returned ${response.status}: ${errorText}`
            );
          }
          return response.json();
        })
        .then(data => {
          console.log('Received response:', data);
          if (data.error) {
            throw new Error(data.error);
          }
          handleParsedResponse(data.response);
        })
        .catch(error => {
          console.error('Request failed:', error);
          if (error.message.includes('Failed to fetch')) {
            showError('Unable to connect to server. Please make sure the backend is running.');
          } else {
            showError(`Error: ${error.message}`);
          }
        });
    }
  
    // Helper functions
    function showError(message) {
      const responseDiv = document.getElementById('response');
      if (responseDiv) {
        responseDiv.innerHTML = `<div class="error-message">${message}</div>`;
        adjustPopupSize();
      }
    }
  
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
  });
  
  
  
  // dropdown
  document.addEventListener('DOMContentLoaded', function () {
    const signupButton = document.getElementById('signupButton');
    const dropdownMenu = document.getElementById('dropdownMenu');
    const editButton = document.getElementById('editButton');
    const editDropdownMenu = document.getElementById('editDropdownMenu');
    const accountButton = document.getElementById('accountButton');
    const editDeleteButtons = document.getElementById('editDeleteButtons');
  
    // Initially hide the dropdowns
    dropdownMenu.style.display = 'none';
    editDropdownMenu.style.display = 'none';
    editDeleteButtons.style.display = 'none';
  
    // Toggle Sign Up dropdown
    signupButton.addEventListener('click', function (e) {
      e.stopPropagation();
      dropdownMenu.style.display = dropdownMenu.style.display === 'none' ? 'block' : 'none';
      editDropdownMenu.style.display = 'none'; // Hide Edit dropdown when Sign Up is clicked
    });
  
    // Toggle Edit dropdown
    editButton.addEventListener('click', function (e) {
      e.stopPropagation();
      editDropdownMenu.style.display = editDropdownMenu.style.display === 'none' ? 'block' : 'none';
      dropdownMenu.style.display = 'none'; // Hide Sign Up dropdown when Edit is clicked
    });
  
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
  });
  
  
  
  document.getElementById('editButton1').addEventListener('click', function () {
    window.location.href = 'topup.html'; // Replace 'topup.html' with your URL
  });
  
  
  
  
  
  
  
  
  // pricing.js
  
  document.addEventListener('DOMContentLoaded', function () {
    const monthlyBtn = document.getElementById('monthlyBtn');
    const yearlyBtn = document.getElementById('yearlyBtn');
  
    // Toggle between monthly and yearly
    monthlyBtn.addEventListener('click', function () {
      monthlyBtn.classList.add('active');
      yearlyBtn.classList.remove('active');
      updatePrices('monthly');
    });
  
    yearlyBtn.addEventListener('click', function () {
      yearlyBtn.classList.add('active');
      monthlyBtn.classList.remove('active');
      updatePrices('yearly');
    });
  
    // Function to update prices based on billing period
    function updatePrices(period) {
      const prices = {
        monthly: {
          creator: '₹499',
          masterMind: '₹999'
        },
        yearly: {
          creator: '₹4,999',
          masterMind: '₹9,999'
        }
      };
  
      // Update prices on the cards
      const creatorPrice = document.querySelector('.pricing-card:nth-child(2) .text-2xl');
      const masterPrice = document.querySelector('.pricing-card:nth-child(3) .text-2xl');
  
      creatorPrice.textContent = prices[period].creator;
      masterPrice.textContent = prices[period].masterMind;
  
      // Add a small animation to price changes
      [creatorPrice, masterPrice].forEach(el => {
        el.style.transform = 'scale(1.1)';
        setTimeout(() => {
          el.style.transform = 'scale(1)';
        }, 200);
      });
    }
  });
  
  // Assuming the user ID is available, otherwise you can retrieve it from localStorage, cookies, etc.
  const userId = localStorage.getItem('userId');
  const token = localStorage.getItem('token');
  console.log("token:" + token);
  // const userId = 'user123'; // Replace with the actual user ID (from session, localStorage, etc.)
  
  // Fetch User Profile data
  fetch(`http://127.0.0.1:3001/api/users/profile/${userId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}` // Add the Authorization header with the token
    }
  })
    .then(response => response.json())
    .then(data => {
      // Assuming the API response has a 'name' field for the user's name
      const userName = data.data.user.name;
      console.log("data:" + data.data.user.name);
      // Update the "Hii Nikhil" button with the user's name
      document.getElementById('signupButton').textContent = `Hii ${userName}`; 
      // signupButton
      // document.getElementById('signupButton').textContent = ` ${userName}`;
    })
    .catch(error => console.error('Error fetching user profile:', error));
  
  // Function to fetch and update credit display
  async function updateCreditDisplay() {
    try {
      const response = await fetch(`http://127.0.0.1:3001/api/token-types/${userId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        }
      });
      const data = await response.json();
      const tokensReceived = data.data.token_received;
      const tokensUsed = data.data.tokens_used;
      document.getElementById('editButton').textContent = `${tokensReceived - tokensUsed} Credits`;
    } catch (error) {
      console.error('Error updating credit display:', error);
    }
  }
    
  
  
  
  // This is the function that will be triggered when the "Generate" button is clicked
  function handleCreditDeduction(feature) {
    // First fetch available credits for the feature
    fetch('http://127.0.0.1:3001/api/credit/credits', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}` // Add the Authorization header with the token
      }
    })
      .then(response => response.json())
      .then(data => {
        // console.log("creditdata:"+data);
        const featureCredit = data.data.find(credit => credit.feature === feature);
        console.log("creditfeture:"+featureCredit);
        if (!featureCredit) {
          console.error('Feature not found');
          return;
        }
  
        // Then check and update user's token balance
        fetch(`http://127.0.0.1:3001/api/token-types/${userId}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
          }
        })
          .then(response => response.json())
          .then(data => {
            console.log("data recvd:"+data.data);
            const tokensReceived = data.data.token_received;
            const tokensUsed = data.data.tokens_used;
  
            // document.getElementById('editButton').textContent = `${tokensReceived - tokensUsed} Credits`;
  
            if (tokensReceived <= tokensUsed) {
              alert("You are out of tokens!");
              document.getElementById('sendButton').disabled = true; // Disable the send button
              return;
            }
  
            if (tokensReceived - tokensUsed >= featureCredit.credits) {
              const updatedTokensUsed = tokensUsed + featureCredit.credits;
  
              fetch(`http://127.0.0.1:3001/api/token-types/${userId}`, {
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
                .then(async (updateData)  => {
                  console.log(`Credits deducted for ${feature}:`, featureCredit.credits);
                  // Re-enable the send button if tokens are sufficient
                  document.getElementById('sendButton').disabled = false;
                  //  Refresh credits display immediately after deduction
                    await updateCreditDisplay();
                    
                    resolve('Success');
                })
                .catch(error => console.error('Error updating tokens:', error));
            } else {
              alert(`Not enough tokens for ${feature}`);
            }
          });
      })
      .catch(error => console.error('Error fetching credits:', error));
  }
  
  // Feature usage tracking
  let promptUsed = false;
  let advancedOptionsUsed = false;
  let imageGuidanceUsed = false;
  let advancedOptionsSelected = new Set();
  
  // Event listener for basic prompt
  document.getElementById('promptInput').addEventListener('change', function () {
    promptUsed = true; // Mark basic prompt as used
  });
  
  // Event listeners for advanced option buttons
  const advancedOptionButtons = document.querySelectorAll('.dropdown-card');
  advancedOptionButtons.forEach(button => {
    button.addEventListener('click', function () {
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
  document.getElementById('imageUpload').addEventListener('change', function () {
    const allowedExtensions = ['jpg', 'jpeg', 'png', 'svg'];
  
    if (this.files.length > 0) {
      const file = this.files[0];
      const fileExtension = file.name.split('.').pop().toLowerCase();
  
      if (!allowedExtensions.includes(fileExtension)) {
        alert('Only image files (jpg, jpeg, png) are allowed!');
        this.value = ''; // Clear the file input
        imageGuidanceUsed = false; // Reset usage tracking
        return;
      }
  
      imageGuidanceUsed = true; // Mark image guidance as used
    } else {
      imageGuidanceUsed = false; // Reset if no files are selected
    }
  });
  
  // Event listener for generate button
  document.getElementById('sendButton').addEventListener('click', async function () {
    try {
      // Disable the input area while processing
      document.getElementById('promptInput').disabled = true;
  
      // Log the current usage status
      console.log('Generating with the following options:');
      console.log('Prompt used:', promptUsed);
      console.log('Advanced options used:', advancedOptionsUsed);
      console.log('Image guidance used:', imageGuidanceUsed);
  
      // Check if the basic prompt is used
      if (promptUsed) {
        console.log('Deducting credit for basic prompt');
        await handleCreditDeduction('basic_prompt');
      }
  
      // If any advanced options are selected, deduct credits for each
      if (advancedOptionsUsed && advancedOptionsSelected.size > 0) {
        // Loop through the selected advanced options and deduct credits
        for (const optionId of advancedOptionsSelected) {
          console.log(`Deducting credit for: advanced_prompt_${optionId}`);
          await handleCreditDeduction(`advanced_prompt_${optionId}`);
        }
      }
  
      // Check if image guidance is used
      if (imageGuidanceUsed) {
        console.log('Deducting credit for image guidance');
        await handleCreditDeduction('image_prompt');
      }
  
      // If all options are used, deduct credits for the complete prompt
      if (promptUsed && advancedOptionsUsed && imageGuidanceUsed) {
        console.log('Deducting credit for complete prompt');
        await handleCreditDeduction('complete_prompt');
      }
  
      // Reset all tracking after successful generation
      promptUsed = false;
      advancedOptionsUsed = false;
      imageGuidanceUsed = false;
      advancedOptionsSelected.clear();
  
      // Reset visual state of buttons
      advancedOptionButtons.forEach(button => {
        button.classList.remove('selected');
      });
  
      // Clear the image upload input
      document.getElementById('imageUpload').value = '';
  
      // Final refresh of credits display
      await updateCreditDisplay();
  
      // Enable the input area after processing
      document.getElementById('promptInput').disabled = false;
  
      // Reset the prompt input field after generating prompts
      document.getElementById('promptInput').value = '';
  
    } catch (error) {
      console.error('Error during credit deductions:', error);
      // Refresh credits display even if there's an error
      await updateCreditDisplay();
  
      // Enable the input area in case of error
      document.getElementById('promptInput').disabled = false;
    }
  });
  
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
      if (logoutButton) {
        // Remove the inline onclick attribute
        logoutButton.removeAttribute('onclick');
  
        // Add event listener
        logoutButton.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          logout();
        });
      } else {
        console.warn('Logout button not found in the DOM');
      }
  
      // Make logout function available globally
      window.logout = logout;