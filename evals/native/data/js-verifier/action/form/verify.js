// Verify that the search box (textarea#APjFqb) contains the expected text
// Using IIFE to avoid variable redeclaration errors
(function() {
  const textarea = document.querySelector('textarea#APjFqb');
  return textarea && textarea.value === 'Chrome DevTools automation testing';
})()