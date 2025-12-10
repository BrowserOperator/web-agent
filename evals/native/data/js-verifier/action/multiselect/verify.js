// Validation: Check if both Volvo and Audi are selected in the multi-select dropdown
// The select element is inside the iframeResult iframe (typical W3Schools structure)
(() => {
  const iframe = document.getElementById('iframeResult');
  const selectElement = iframe?.contentDocument?.querySelector('select[name="cars"]');
  if (!selectElement) {
    return false;
  }
  const selectedOptions = Array.from(selectElement.selectedOptions).map(opt => opt.value.toLowerCase());
  return selectedOptions.includes('volvo') && selectedOptions.includes('audi');
})()