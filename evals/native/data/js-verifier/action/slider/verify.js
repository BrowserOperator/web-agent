// Check if the slider value is set to approximately 75
// jQuery UI sliders are in an iframe on this page
(() => {
  const iframe = document.querySelector('iframe.demo-frame');
  if (!iframe || !iframe.contentDocument || !iframe.contentWindow) {
    return false;
  }

  const $ = iframe.contentWindow.$;
  if (!$) {
    return false;
  }

  const slider = iframe.contentDocument.querySelector('#slider');
  if (!slider) {
    return false;
  }

  const value = $(slider).slider('option', 'value');
  // Accept values within reasonable range of 75 (60-80)
  return value >= 60 && value <= 80;
})()