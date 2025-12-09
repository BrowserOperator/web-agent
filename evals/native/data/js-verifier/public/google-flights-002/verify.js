// Validation: Find two way business class flight options from New York to Singapore for 2 persons, June 1-30
// Check that the page shows flight search results with the correct parameters
// Key differentiators: "2 adults" and June dates only appear in AFTER state
// Using IIFE to avoid variable re-declaration errors on repeated execution

(function() {
  const pageText = document.body.innerText.toLowerCase();

  // Check 1: Look for 2 adults (how Google Flights displays 2 passengers)
  // This is a key distinguisher - BEFORE tab doesn't have this
  const hasTwoAdults = pageText.includes('2 adults');

  // Check 2: Look for June dates (Jun 1 format)
  // This is a key distinguisher - BEFORE tab doesn't have specific June dates
  const hasJuneDates = pageText.includes('jun 1') || pageText.includes('june 1');

  // Check 3: Look for business class indicator
  const hasBusiness = pageText.includes('business');

  // Check 4: Look for Singapore as destination
  const hasSingapore = pageText.includes('singapore');

  // All key conditions must be true for validation to pass
  return hasTwoAdults && hasJuneDates && hasBusiness && hasSingapore;
})()