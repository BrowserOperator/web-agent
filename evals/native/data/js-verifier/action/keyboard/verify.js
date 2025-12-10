// Check if the "Accessibility Features" heading has tabindex attribute
// This indicates successful keyboard navigation to the menu item
(function() {
  const heading = document.querySelector('h2#accessibilityfeatures');
  return heading && heading.getAttribute('tabindex') === '-1';
})()