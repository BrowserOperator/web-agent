// Check if the "I have a bike" checkbox is checked
// The checkbox is inside the iframeResult iframe (W3Schools Try It editor)
(() => {
  const iframe = document.getElementById('iframeResult');
  if (!iframe || !iframe.contentDocument) return false;
  const checkbox = iframe.contentDocument.querySelector('input[type="checkbox"][value="Bike"]');
  return checkbox ? checkbox.checked === true : false;
})()