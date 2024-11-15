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

  fetch('http://localhost:5000/get_categories')
    .then(response => response.json())
    .then(categories => {
      console.log('Categories:', categories);
      categories.forEach(category => {
        const categoryCard = createCategoryCard(category);
        categoriesContainer.appendChild(categoryCard);
      });
    })
    .catch(error => {
      console.error('Error fetching categories:', error);
      categoriesContainer.textContent = `Failed to load categories. Error: ${error.message}`;
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

  function createCategoryCard(category) {
    const categoryCard = document.createElement('div');
    categoryCard.className = 'category-card';
    const categoryTitle = document.createElement('div');
    categoryTitle.className = 'category-title';
    categoryTitle.textContent = category.name;
    categoryCard.appendChild(categoryTitle);
    categoryCard.id = 'category-card'
    const dropdownContainer = createDropdown(category);
    categoryCard.appendChild(dropdownContainer);

    return categoryCard;
  }

  function updateDropdownButton(dropdownButton, selectedItem) {
    const nameContainer = dropdownButton.querySelector('span');
    nameContainer.textContent = selectedItem.querySelector('.dropdown-card-select').textContent;
  }

  function createDropdown(category) {
    const dropdownContainer = document.createElement('div');
    dropdownContainer.className = 'dropdown';

    const dropdownButton = document.createElement('button');
    dropdownButton.className = 'dropdown-button';
    dropdownButton.innerHTML = `
        <div class="dropdown-button-content">
            <span>Select</span>
        </div>
    `;

    const dropdownContent = document.createElement('div');
    dropdownContent.className = 'dropdown-content';

    const horizontalContainer = document.createElement('div');
    horizontalContainer.className = 'dropdown-horizontal-container';

    category.items.forEach(item => {
      const card = document.createElement('div');
      card.className = 'dropdown-card';

      const selectButton = document.createElement('button');
      selectButton.className = 'dropdown-card-select';
      selectButton.textContent = item.name;

      card.appendChild(selectButton);

      selectButton.addEventListener('click', function (event) {
        event.stopPropagation();
        horizontalContainer.querySelectorAll('.dropdown-card').forEach(c =>
          c.classList.remove('selected')
        );
        card.classList.add('selected');
        updateDropdownButton(dropdownButton, card);
        dropdownContent.style.display = 'none';
      });

      horizontalContainer.appendChild(card);
    });

    dropdownContent.appendChild(horizontalContainer);
    dropdownContainer.appendChild(dropdownButton);
    dropdownContainer.appendChild(dropdownContent);

    dropdownButton.addEventListener('click', function (event) {
      event.stopPropagation();
      closeAllDropdowns();
      dropdownContent.style.display =
        dropdownContent.style.display === 'block' ? 'none' : 'block';
    });

    return dropdownContainer;
  }


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

    // Log the data being sent
    console.log('Sending data:', {
      prompt,
      selectedCategories,
      selectedAIType
    });

    // Validate inputs
    if (!prompt && (!imageUpload || imageUpload.files.length === 0)) {
      showError('Please enter a prompt or upload an image.');
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

  // Show Edit/Delete buttons when Account button is clicked
  accountButton.addEventListener('click', function (e) {
    e.stopPropagation();
    signupButton.style.display = 'none'; // Hide Sign Up button
    editDeleteButtons.style.display = 'block'; // Show Edit/Delete buttons
  });

  // Close dropdowns when clicking outside
  document.addEventListener('click', function (e) {
    if (e.target !== signupButton && e.target !== editButton && !dropdownMenu.contains(e.target) && !editDropdownMenu.contains(e.target)) {
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
const token = localStorage.getItem('userToken');
console.log("token:" + token);
// const userId = 'user123'; // Replace with the actual user ID (from session, localStorage, etc.)

// Fetch User Profile data
fetch(`http://127.0.0.1:3000/api/users/profile/${userId}`, {
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
    document.getElementById('deleteButton').textContent = `Hii ${userName}`; 
    // signupButton
    document.getElementById('signupButton').textContent = ` ${userName}`;
  })
  .catch(error => console.error('Error fetching user profile:', error));

  // Fetch and update user's token balance
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
    document.getElementById('editButton').textContent = `${tokensReceived - tokensUsed} Credits`;
  })
  .catch(error => console.error('Error fetching token balance:', error));
  



// This is the function that will be triggered when the "Generate" button is clicked
function handleCreditDeduction(feature) {
  // First fetch available credits for the feature
  fetch('http://127.0.0.1:3000/api/credit/credits', {
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
      fetch(`http://127.0.0.1:3000/api/token-types/${userId}`, {
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

          document.getElementById('editButton').textContent = `${tokensReceived - tokensUsed} Credits`;

          if (tokensReceived <= tokensUsed) {
            alert("You are out of tokens!");
            document.getElementById('sendButton').disabled = true; // Disable the send button
            return;
          }

          if (tokensReceived - tokensUsed >= featureCredit.credits) {
            const updatedTokensUsed = tokensUsed + featureCredit.credits;

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
              .then(updateData => {
                console.log(`Credits deducted for ${feature}:`, featureCredit.credits);
                // Re-enable the send button if tokens are sufficient
                document.getElementById('sendButton').disabled = false;
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
document.getElementById('promptInput').addEventListener('change', function() {
  if (!promptUsed) {
    handleCreditDeduction('basic_prompt');
    promptUsed = true;
  }
});

// Event listeners for advanced option buttons
const advancedOptionButtons = document.querySelectorAll('.category-card'); // Assuming each button has class 'category-card'
advancedOptionButtons.forEach(button => {
  button.addEventListener('click', function() {
    const optionId = this.getAttribute('data-option-id'); // Unique identifier for each option
    
    if (!advancedOptionsSelected.has(optionId)) {
      // If this option hasn't been selected before
      if (!advancedOptionsUsed) {
        // Only deduct tokens the first time any advanced option is selected
        handleCreditDeduction('advanced_prompt');
        advancedOptionsUsed = true;
      }
      advancedOptionsSelected.add(optionId);
      
      // Add selected state to button
      this.classList.add('selected');
    } else {
      // Option is being deselected
      advancedOptionsSelected.delete(optionId);
      this.classList.remove('selected');
      
      // If no options are selected anymore, reset the advanced options usage
      if (advancedOptionsSelected.size === 0) {
        advancedOptionsUsed = false;
      }
    }
  });
});

// Event listener for image upload
document.getElementById('imageUpload').addEventListener('change', function () {
  const allowedExtensions = ['jpg', 'jpeg', 'png'];
  
  // Check if files are selected
  if (this.files.length > 0) {
    const file = this.files[0];
    const fileExtension = file.name.split('.').pop().toLowerCase(); // Get file extension

    if (!allowedExtensions.includes(fileExtension)) {
      alert('Only image files (jpg, jpeg, png) are allowed!');
      this.value = ''; // Clear the file input
      imageGuidanceUsed = false; // Reset usage tracking
      return;
    }

    if (!imageGuidanceUsed) {
      handleCreditDeduction('image_prompt');
      imageGuidanceUsed = true;
    }
  } else {
    imageGuidanceUsed = false;
  }
});


// Event listener for send button
document.getElementById('sendButton').addEventListener('click', function() {
  if (promptUsed && advancedOptionsUsed && imageGuidanceUsed) {
    handleCreditDeduction('complete_prompt');
  }
  
  // Reset all tracking
  promptUsed = false;
  advancedOptionsUsed = false;
  imageGuidanceUsed = false;
  advancedOptionsSelected.clear();
  
  // Reset visual state of buttons
  advancedOptionButtons.forEach(button => {
    button.classList.remove('selected');
  });
});

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