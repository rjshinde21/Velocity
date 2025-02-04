export const StyleButtonManager = {
    init() {
      this.loadSavedStyle();
      this.setupStylePersistence();
    },
  
    loadSavedStyle() {
      const savedStyle = localStorage.getItem('velocitySelectedStyle');
      if (savedStyle) {
        window.velocityState.styleType = savedStyle;
        this.updateStyleButtons(savedStyle);
      }
    },
  
    setupStylePersistence() {
      document.addEventListener('click', (e) => {
        const styleButton = e.target.closest('.velocity-style-button');
        if (styleButton) {
          const style = styleButton.dataset.style;
          this.setActiveStyle(style);
        }
      });
    },
  
    setActiveStyle(style) {
      localStorage.setItem('velocitySelectedStyle', style);
      window.velocityState.styleType = style;
      this.updateStyleButtons(style);
    },
  
    updateStyleButtons(activeStyle) {
      document.querySelectorAll('.velocity-style-button').forEach(button => {
        button.classList.toggle('active', button.dataset.style === activeStyle);
      });
    }
  };