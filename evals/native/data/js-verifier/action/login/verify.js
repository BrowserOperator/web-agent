// Validate that username and password fields are filled correctly
// Using IIFE to avoid variable redeclaration errors
(() => {
  const usernameField = document.querySelector('#username');
  const passwordField = document.querySelector('#password');

  // Check both fields exist and have correct values
  return usernameField &&
    passwordField &&
    usernameField.value === 'tomsmith' &&
    passwordField.value === 'SuperSecretPassword!';
})()