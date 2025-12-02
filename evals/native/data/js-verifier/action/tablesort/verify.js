// Validation: Check if the table has been sorted by clicking the "Name" column header
// The Name column header should have aria-sort="descending" after clicking (was "ascending" before)
// Also verify the sorting class changed from dt-ordering-asc to dt-ordering-desc

(() => {
  // Find the Name column header in the table
  const table = document.querySelector('table#example');
  if (!table) return false;

  // Find the header cell with aria-sort attribute that contains "Name"
  const nameHeader = table.querySelector('thead th[aria-sort]');
  if (!nameHeader) return false;

  // Check if it's sorted descending (after clicking on ascending column)
  const ariaSort = nameHeader.getAttribute('aria-sort');
  const hasDescendingSort = ariaSort === 'descending';

  // Also check the class for dt-ordering-desc
  const hasOrderingDescClass = nameHeader.classList.contains('dt-ordering-desc');

  // Both conditions should be true after clicking the Name header
  return hasDescendingSort && hasOrderingDescClass;
})()