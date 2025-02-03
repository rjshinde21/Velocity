class StyleSelector {
    constructor(parent) {
      this.parent = parent;
      this.styles = ['Descriptive', 'Creative', 'Professional', 'Concise'];
    }
  
    create() {
      const container = document.createElement('div');
      container.className = 'velocity-style-buttons';
      this.styles.forEach(style => this.createStyleButton(style, container));
      return container;
    }
  
    createStyleButton(style, container) {
        const styleButton = document.createElement('button');
        styleButton.className = 'velocity-style-button';
        styleButton.dataset.style = style.name.toLowerCase();
      
        // Create grid layout container
        const gridContainer = document.createElement('div');
        gridContainer.className = 'velocity-style-grid';
      
        // Create and set up image container
        const imageContainer = document.createElement('div');
        imageContainer.className = 'velocity-style-image';
        const img = document.createElement('img');
        img.src = chrome.runtime.getURL(style.imagePath);
        img.alt = style.name;
        imageContainer.appendChild(img);
      
        // Create text container
        const textContainer = document.createElement('div');
        textContainer.className = 'velocity-style-text';
      
        // Add title and description
        const titleSpan = document.createElement('span');
        titleSpan.className = 'velocity-style-button-title';
        titleSpan.textContent = style.name;
      
        const descriptionSpan = document.createElement('span');
        descriptionSpan.className = 'velocity-style-description';
        descriptionSpan.textContent = style.description;
      
        // Assemble components
        textContainer.appendChild(titleSpan);
        textContainer.appendChild(descriptionSpan);
        gridContainer.appendChild(imageContainer);
        gridContainer.appendChild(textContainer);
        styleButton.appendChild(gridContainer);
      
        // Add click handler
        styleButton.addEventListener('click', async (e) => {
          e.preventDefault();
          e.stopPropagation();
          
          const currentStyle = styleButton.dataset.style;
          const isCurrentlyActive = styleButton.classList.contains('active');
          
          // Remove active class from all buttons
          container.querySelectorAll('.velocity-style-button').forEach(btn => {
            btn.classList.remove('active');
          });
      
          if (!isCurrentlyActive) {
            styleButton.classList.add('active');
            window.velocityState.styleType = currentStyle;
            
            // Handle text enhancement if content exists
            const selectedText = getSelectedText(this.input);
            const fullText = this.input.value || this.input.textContent || '';
            
            if (!selectedText && !fullText) {
              messageEl.textContent = `Please enter some text first!`;
              return;
            }
      
            try {
              showLoading();
              const textToEnhance = selectedText || fullText;
              const enhancedText = await enhancePrompt(textToEnhance);
      
              // Update input content
              if (this.input.value !== undefined) {
                this.input.value = enhancedText;
              } else {
                this.input.textContent = enhancedText;
              }
      
              // Trigger input events
              const inputEvent = new Event('input', { bubbles: true });
              this.input.dispatchEvent(inputEvent);
      
              // Save style preference
              await chrome.storage.local.set({ selectedStyle: currentStyle });
      
            } catch (error) {
              messageEl.textContent = 'Enhancement failed. Please try again.';
              messageEl.style.color = '#ff4444';
              setTimeout(() => {
                messageEl.style.color = '';
                messageEl.textContent = 'Select a style that best matches your needs';
              }, 3000);
            } finally {
              hideLoading();
              updateButtonAnimations(button, this.input);
            }
          } else {
            // Reset style selection
            window.velocityState.styleType = '';
            messageEl.textContent = 'Please select a style that best matches your needs';
            await chrome.storage.local.remove('selectedStyle');
          }
        });
      
        container.appendChild(styleButton);
      }
  }