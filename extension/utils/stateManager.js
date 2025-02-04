export const StateManager = {
    init() {
      if (!window.velocityState) {
        window.velocityState = {};
      }
      this.loadSavedState();
    },
  
    loadSavedState() {
      const savedState = localStorage.getItem('velocityState');
      if (savedState) {
        window.velocityState = { ...window.velocityState, ...JSON.parse(savedState) };
      }
    },
  
    saveState() {
      localStorage.setItem('velocityState', JSON.stringify(window.velocityState));
    }
  };
  
  // Export main initialization function
  export function initializeThemeSystem() {
    StateManager.init();
    ThemeManager.init();
    StyleButtonManager.init();
  }