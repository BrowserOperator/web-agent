// Validation: Check if "JavaScript" was successfully entered/selected in the autocomplete
// Objective: Type "Java" and select "JavaScript" from the autocomplete suggestions
//
// Since the autocomplete demo may be in an iframe or the main document,
// we check both locations

(() => {
  // Helper function to check for the input value
  const checkInput = (doc) => {
    const input = doc.querySelector('#tags');
    return input && input.value.trim() === 'JavaScript';
  };

  // Check main document first
  if (checkInput(document)) {
    return true;
  }

  // Check all iframes
  const iframes = document.querySelectorAll('iframe');
  for (const iframe of iframes) {
    try {
      if (iframe.contentDocument && checkInput(iframe.contentDocument)) {
        return true;
      }
    } catch (e) {
      // Cross-origin iframe, skip it
      continue;
    }
  }

  // Not found or value doesn't match
  return false;
})()
