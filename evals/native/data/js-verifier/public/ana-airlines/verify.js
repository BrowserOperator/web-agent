// Validation for: Find a roundtrip flight from Singapore to Tokyo from April 10 to April 20 for 1 adult
// This checks for the presence of flight search results with the correct parameters

(() => {
  // Check for the search results page by verifying hidden inputs with flight search details
  const segmentCode = document.querySelector('#criteo_segment_code');
  const departureDate = document.querySelector('#criteo_departure_date');
  const arrivalDate = document.querySelector('#criteo_arrival_date');
  const searchMode = document.querySelector('#criteo_search_mode');
  const adultCount = document.querySelector('#criteo_adult_count');
  const boardingClass = document.querySelector('#criteo_boarding_class');

  // Verify all required elements exist and have correct values
  const hasCorrectRoute = segmentCode && segmentCode.value === 'SIN_TYO';
  const hasCorrectDeparture = departureDate && departureDate.value === '20260410';
  const hasCorrectArrival = arrivalDate && arrivalDate.value === '20260420';
  const hasRoundTrip = searchMode && searchMode.value === 'ROUND_TRIP';
  const hasOneAdult = adultCount && adultCount.value === '1';
  const hasEconomyClass = boardingClass && boardingClass.value === 'eco';

  // Also verify the page title indicates search results
  const isSearchResultsPage = document.title.includes('Search Results');

  // All conditions must be true - using return since this is an IIFE
  return hasCorrectRoute && hasCorrectDeparture && hasCorrectArrival && hasRoundTrip && hasOneAdult && hasEconomyClass && isSearchResultsPage;
})()