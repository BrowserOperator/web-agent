// Validate that hotels in Madeira were searched for June 1-29 with 2 adults and 1 child (10 years old)
(() => {
  // Check if we're on the search results page
  const isSearchResultsPage = document.body && document.body.id === 'b2searchresultsPage';
  if (!isSearchResultsPage) {
    return false;
  }

  // Get page text content for validation
  const pageText = document.body.innerText || document.body.textContent || '';

  // Check for Madeira destination (the input field or breadcrumb should contain Madeira)
  const destinationInput = document.querySelector('input[name="ss"]');
  const destinationValue = destinationInput ? destinationInput.value.toLowerCase() : '';
  const hasMadeira = destinationValue.includes('madeir') ||
                     pageText.toLowerCase().includes('madeira') ||
                     pageText.toLowerCase().includes('madeirã');

  // Check for June dates (Jun 1 and Jun 29)
  const hasJuneDates = pageText.includes('Jun 1') && pageText.includes('Jun 29');

  // Check for guests: 2 adults and 1 child
  const hasCorrectGuests = pageText.includes('2 adults') && pageText.includes('1 child');

  // All conditions must be met
  return hasMadeira && hasJuneDates && hasCorrectGuests;
})()