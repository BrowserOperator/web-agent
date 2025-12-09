// Validation: Find one way flight options from Austin to Paris at May 20
// Check multiple indicators that flight search results are displayed
(() => {
  const title = document.title;
  const url = window.location.href;

  // Check title contains flight route (AUS to PAR) and date (5/20)
  const titleHasAUS = title.includes('AUS');
  const titleHasPAR = title.includes('PAR');
  const titleHasDate = title.includes('5/20');

  // Check URL contains the flight route and date
  const urlHasRoute = url.includes('/flights/AUS-PAR/');
  const urlHasDate = url.includes('2026-05-20');

  // Ensure this is a ONE-WAY flight, not round-trip
  // Round-trip URLs have two dates: /2026-05-20/2026-05-20
  // One-way URLs have only one date: /2026-05-20?
  const isOneWay = /\/flights\/AUS-PAR\/2026-05-20($|\?)/.test(url) ||
                   (url.includes('2026-05-20') && !url.includes('2026-05-20/2026'));

  // Check for flight results list wrapper link (added when results page loads)
  const hasFlightResults = document.querySelector('a[href="#flight-results-list-wrapper"]') !== null;

  return titleHasAUS && titleHasPAR && titleHasDate && urlHasRoute && urlHasDate && isOneWay && hasFlightResults;
})()