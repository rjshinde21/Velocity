class Popup {
    constructor(button) {
      this.button = button;
      this.popup = null;
      this.messageEl = null;
    }
  
    create() {
      this.popup = document.createElement('div');
      this.popup.className = 'velocity-popup';
      this.createMessage();
      this.createStyleSelector();
      return this.popup;
    }
  
    createMessage() {
      this.messageEl = document.createElement('div');
      this.messageEl.className = 'velocity-message';
    }
  
    createStyleSelector() {
      const selector = new StyleSelector(this.popup);
      selector.create();
    }
  }