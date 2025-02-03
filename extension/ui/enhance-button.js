class EnhanceButton {
    constructor(inputElement, platformInfo) {
        this.input = inputElement;
        this.platform = platformInfo;
        this.button = null;
      }

      create() {
        this.button = document.createElement('button');
        this.button.className = 'velocity-enhance-button';
        this.setupStyles();
        this.setupEvents();
        return this.button;
      }
    
      setupStyles() {
        this.button.style.cssText = baseStyles.button;
      }

      setupEvents() {
        this.button.addEventListener('click', this.handleClick.bind(this));
        this.button.addEventListener('mouseenter', this.handleHover.bind(this));
      }
}