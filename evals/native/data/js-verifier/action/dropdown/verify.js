// Validation: Check if "Audi" is selected in the car brands dropdown
// The objective is to verify that the dropdown with id="cars" has value="audi" selected
// The dropdown is inside an iframe with id="iframeResult"

// Wrap in an IIFE to avoid variable conflicts
(() => {
  // Find the iframe and access its content document
  const iframe = document.querySelector('iframe#iframeResult');
  const iframeDoc = iframe && iframe.contentDocument;

  // Find the dropdown element inside the iframe
  const dropdown = iframeDoc && iframeDoc.querySelector('select#cars');

  // Return true if dropdown exists and has the value "audi" selected
  return dropdown && dropdown.value === 'audi';
})()