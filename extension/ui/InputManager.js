class InputManager {
    constructor(inputElement) {
      this.input = inputElement;
      this.platformInfo = window.velocityState?.platformInfo;
      this.resizeObserver = null;
      this.setupResizing();
    }
  
    setupResizing() {
      this.resizeObserver = new ResizeObserver(() => {
        const scrollPos = window.scrollY;
        this.input.style.height = 'auto';
        this.input.style.height = `${this.input.scrollHeight}px`;
        
        const wrapper = this.input.closest('.velocity-wrapper');
        if (wrapper) {
          wrapper.style.height = this.input.style.height;
          const button = wrapper.querySelector('.velocity-enhance-button');
          if (button) button.style.bottom = '8px';
        }
        window.scrollTo(0, scrollPos);
      });
  
      this.resizeObserver.observe(this.input);
      this.input.addEventListener('input', () => this.updateSize());
      this.updateSize();
    }
  
    handleSelection() {
      if (this.input.tagName === 'TEXTAREA' || this.input.tagName === 'INPUT') {
        return this.input.value.substring(this.input.selectionStart, this.input.selectionEnd);
      }
      
      const selection = window.getSelection();
      if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        if (this.input.contains(range.commonAncestorContainer)) {
          return selection.toString();
        }
      }
      return '';
    }
  
    updateContent(newContent) {
      if (this.input.value !== undefined) {
        this.input.value = newContent;
      } else {
        this.input.textContent = newContent;
      }
  
      const inputEvent = new Event('input', { bubbles: true });
      this.input.dispatchEvent(inputEvent);
  
      if (this.platformInfo?.platform === 'claude') {
        this.input.dispatchEvent(new Event('change', { bubbles: true }));
        this.input.focus();
        
        if (this.input.getAttribute('contenteditable') === 'true') {
          this.input.dispatchEvent(new KeyboardEvent('keyup', {
            bubbles: true,
            key: 'Space',
            keyCode: 32
          }));
        }
      }
    }
  
    updateSize() {
      if (!this.input) return;
      this.input.style.height = 'auto';
      this.input.style.height = `${this.input.scrollHeight}px`;
    }
  
    cleanup() {
      if (this.resizeObserver) {
        this.resizeObserver.disconnect();
      }
    }
  }