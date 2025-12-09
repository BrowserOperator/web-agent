// Validate that ONE-WAY ECONOMY flight search from New York to Warsaw for JULY 15 was performed
// Key indicators:
// 1. Page title contains "New York to Warsaw | Google Flights"
// 2. Trip type is "One way" (not "Round trip")
// 3. Departure date is July 15
// 4. Cabin class is Economy (not Business, First, or Premium economy)
(() => {
  const pageTitle = document.title;
  const titleCorrect = pageTitle.includes('New York') && pageTitle.includes('Warsaw') && pageTitle.includes('Google Flights');

  const spans = Array.from(document.querySelectorAll('span'));

  // Check trip type - look for span with "One way" text
  const tripTypeSpan = spans.find(s => s.textContent === 'Round trip' || s.textContent === 'One way');
  const isOneWay = tripTypeSpan && tripTypeSpan.textContent === 'One way';

  // Check cabin class - first matching cabin span indicates selected class
  const cabinSpan = spans.find(s => ['Economy', 'Business', 'First', 'Premium economy'].includes(s.textContent));
  const isEconomy = cabinSpan && cabinSpan.textContent === 'Economy';

  // Check that the departure date is July 15
  const inputs = Array.from(document.querySelectorAll('input'));
  const departureInput = inputs.find(i => i.getAttribute('aria-label') === 'Departure');
  let hasValidJulyDate = false;
  if (departureInput && departureInput.value) {
    // Format is like "Wed, Jul 15" - must be exactly July 15
    const match = departureInput.value.match(/Jul\s+(\d+)/);
    if (match) {
      const day = parseInt(match[1], 10);
      hasValidJulyDate = day === 15;
    }
  }

  return titleCorrect && isOneWay && isEconomy && hasValidJulyDate;
})()
