// Check if the "Start" button was clicked and dynamic content loaded successfully
// BEFORE: #start visible, #finish hidden, #loading doesn't exist
// AFTER: #start hidden, #finish visible with "Hello World!", #loading exists but hidden

// Wrap in IIFE to avoid variable redeclaration errors
(() => {
  const startDiv = document.querySelector('#start');
  const finishDiv = document.querySelector('#finish');

  // The key indicator is that #finish must be visible (not display:none)
  // In BEFORE state: #finish has style="display:none"
  // In AFTER state: #finish has style="" (empty, meaning visible)

  const finishVisible = finishDiv && window.getComputedStyle(finishDiv).display !== 'none';
  const hasHelloWorld = finishDiv && finishDiv.textContent.includes('Hello World!');

  // Also check that #start is hidden (it should be hidden after clicking)
  const startHidden = startDiv && window.getComputedStyle(startDiv).display === 'none';

  // Task is complete when finish is visible with correct content AND start is hidden
  return finishVisible && hasHelloWorld && startHidden;
})()