// Validation: Check if the first row in the table is selected
// The objective was to click on the first row to select it
// DataTables adds a "selected" class to the <tr> element when selected

// Use IIFE to avoid variable naming conflicts in page context
(() => {
  const firstRow = document.querySelector('table tbody tr:first-child');
  return firstRow !== null && firstRow.classList.contains('selected');
})();