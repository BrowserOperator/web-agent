// Check if the "Extra Cheese" checkbox is checked
// Using IIFE to avoid variable redeclaration errors
(() => {
  const cheeseCheckbox = document.querySelector('input[type="checkbox"][name="topping"][value="cheese"]');
  return cheeseCheckbox && cheeseCheckbox.checked === true;
})()