// Validation: Check if "Section 2" accordion panel is expanded
// The objective is to verify that Section 2's content is visible (expanded)
// The accordion is inside an iframe with class="demo-frame"

// Wrap in an IIFE to avoid variable conflicts
(() => {
  // Find the iframe and access its content document
  const iframe = document.querySelector('iframe.demo-frame');
  const iframeDoc = iframe && iframe.contentDocument;

  // Find all h3 headers in the accordion
  const headers = iframeDoc && iframeDoc.querySelectorAll('#accordion h3');

  // Find the Section 2 header
  let section2Header = null;
  if (headers) {
    for (const header of headers) {
      if (header.textContent.trim() === 'Section 2') {
        section2Header = header;
        break;
      }
    }
  }

  // Check if Section 2 header exists and has aria-expanded="true"
  // This indicates the accordion panel is expanded
  return section2Header && section2Header.getAttribute('aria-expanded') === 'true';
})()