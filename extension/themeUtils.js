// themeUtils.js
(function() {
    // Create a namespace for our utilities
    window.velocityThemeUtils = {
      THEMES: {
        LIGHT: 'light',
        DARK: 'dark'
      },
  
      themeVariables: {
        light: {
          '--velocity-bg-primary': '#FFFFFF',
          '--velocity-bg-secondary': '#F3F4F6',
          '--velocity-text-primary': '#1A1A1A',
          '--velocity-text-secondary': '#4B5563',
          '--velocity-border': '#E5E7EB',
          '--velocity-accent': '#3B82F6',
          '--velocity-hover': '#E0F2FE',
          '--velocity-shadow': '0 4px 12px rgba(0, 0, 0, 0.1)',
          '--velocity-button-bg': '#FFFFFF',
          '--velocity-button-border': '#E5E7EB'
        },
        dark: {
          '--velocity-bg-primary': '#1A1A1A',
          '--velocity-bg-secondary': '#2D2D2D',
          '--velocity-text-primary': '#FFFFFF',
          '--velocity-text-secondary': '#A3A3A3',
          '--velocity-border': '#404040',
          '--velocity-accent': '#60A5FA',
          '--velocity-hover': '#374151',
          '--velocity-shadow': '0 4px 12px rgba(0, 0, 0, 0.3)',
          '--velocity-button-bg': '#2D2D2D',
          '--velocity-button-border': '#404040'
        }
      },
  
      injectThemeStyles() {
        const styleElement = document.createElement('style');
        styleElement.id = 'velocity-theme-styles';
        
        const themeStyles = `
          /* Light theme (default) */
          :root {
            ${Object.entries(this.themeVariables.light)
              .map(([key, value]) => `${key}: ${value};`)
              .join('\n')}
          }
  
          /* Dark theme */
          :root[data-theme="dark"] {
            ${Object.entries(this.themeVariables.dark)
              .map(([key, value]) => `${key}: ${value};`)
              .join('\n')}
          }
  
          /* Theme transitions */
          .velocity-wrapper,
          .velocity-popup,
          .velocity-enhance-button,
          .velocity-style-button,
          .velocity-message {
            transition: background-color 0.3s ease,
                        color 0.3s ease,
                        border-color 0.3s ease,
                        box-shadow 0.3s ease !important;
          }
  
          /* Theme-aware styles */
          .velocity-popup {
            background-color: var(--velocity-bg-primary) !important;
            color: var(--velocity-text-primary) !important;
            border-color: var(--velocity-border) !important;
            box-shadow: var(--velocity-shadow) !important;
          }
  
          .velocity-style-button {
            background-color: var(--velocity-button-bg) !important;
            border-color: var(--velocity-button-border) !important;
            color: var(--velocity-text-primary) !important;
          }
  
          .velocity-style-button:hover {
            background-color: var(--velocity-hover) !important;
          }
  
          .velocity-style-button.active {
            background-color: var(--velocity-hover) !important;
            border-color: var(--velocity-accent) !important;
          }
  
          .velocity-theme-toggle {
            position: absolute !important;
            top: 8px !important;
            right: 52px !important;
            width: 32px !important;
            height: 32px !important;
            padding: 6px !important;
            background: var(--velocity-button-bg) !important;
            border: 1px solid var(--velocity-button-border) !important;
            border-radius: 6px !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.2s ease !important;
            z-index: 999999 !important;
            color: var(--velocity-text-primary) !important;
          }
  
          .velocity-theme-toggle:hover {
            background: var(--velocity-hover) !important;
            transform: scale(1.05) !important;
          }
        `;
  
        styleElement.textContent = themeStyles;
        document.head.appendChild(styleElement);
      },
  
      loadSavedTheme() {
        const savedTheme = localStorage.getItem('velocityTheme');
        if (savedTheme) {
          this.setTheme(savedTheme);
        }
      },
  
      setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('velocityTheme', theme);
        this.updateThemeToggleIcon(theme);
      },
  
      toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
      },
  
      createThemeToggle() {
        const button = document.createElement('button');
        button.className = 'velocity-theme-toggle';
        button.innerHTML = this.getSunIcon();
  
        button.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          this.toggleTheme();
        });
  
        return button;
      },
  
      updateThemeToggleIcon(theme) {
        const toggles = document.querySelectorAll('.velocity-theme-toggle');
        toggles.forEach(toggle => {
          toggle.innerHTML = theme === 'dark' ? this.getMoonIcon() : this.getSunIcon();
        });
      },
  
      getSunIcon() {
        return `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" 
                     stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="5"/>
                  <line x1="12" y1="1" x2="12" y2="3"/>
                  <line x1="12" y1="21" x2="12" y2="23"/>
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                  <line x1="1" y1="12" x2="3" y2="12"/>
                  <line x1="21" y1="12" x2="23" y2="12"/>
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                </svg>`;
      },
  
      getMoonIcon() {
        return `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" 
                     stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                </svg>`;
      },
  
      initializeThemeSystem() {
        this.injectThemeStyles();
        this.loadSavedTheme();
        return this.createThemeToggle();
      }
    };
  })();