function addButtonToTextAreas() {
  const textAreas = document.querySelectorAll('textarea');
  textAreas.forEach(textArea => {
    if (!textArea.nextElementSibling || !textArea.nextElementSibling.classList.contains('extension-button')) {
      const button = document.createElement('button');
      button.textContent = 'Enhance';
      button.classList.add('extension-button');
      button.addEventListener('click', () => {
        chrome.runtime.sendMessage({
          action: "openPopup",
          text: textArea.value
        });
      });
      textArea.parentNode.insertBefore(button, textArea.nextSibling);
    }
  });
}


// Run the function when the page loads
addButtonToTextAreas();

// Use a MutationObserver to check for dynamically added text areas
const observer = new MutationObserver(addButtonToTextAreas);
observer.observe(document.body, { childList: true, subtree: true });