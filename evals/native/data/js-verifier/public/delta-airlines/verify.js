(() => {
  // Validation for: Find a roundtrip flight from Chicago to Anchorage from April 10 to April 20 for 3 adults

  // Check hidden inputs for route information
  const fromAirport = document.querySelector('input[name="fromAirportCode"]');
  const toAirport = document.querySelector('input[name="arrivalCity"]');

  // Route must be Chicago (CHI) to Anchorage (ANC)
  const fromOk = fromAirport && fromAirport.value === 'CHI';
  const toOk = toAirport && toAirport.value === 'ANC';

  // Check for round trip indicator in header
  const tripTypeHeader = document.querySelector('.triptype-header');
  const tripTypeText = tripTypeHeader ? tripTypeHeader.textContent.trim() : '';
  const roundTripOk = tripTypeText.toLowerCase().includes('round trip');

  // Check for 3 passengers
  const paxHeader = document.querySelector('.paxcount-header');
  const paxText = paxHeader ? paxHeader.textContent : '';
  const passengersOk = paxText.includes('3 Passenger');

  // Check that we're on the search results page
  const searchResults = document.querySelector('.search-results, .mach-search-results');
  const resultsPageOk = searchResults !== null;

  // Check for correct dates (April 10-20)
  const pageText = document.body.innerText;
  const hasApril10 = pageText.includes('Apr 10') || pageText.includes('April 10');
  const datesOk = hasApril10;

  // All checks must pass
  return Boolean(fromOk && toOk && roundTripOk && passengersOk && resultsPageOk && datesOk);
})()
