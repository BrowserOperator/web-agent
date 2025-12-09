// Validation: Find roundtrip flight options from Houston to Madrid from May 15 to June 15
// for a family of two adults and one child
// Key indicators:
// 1. Page title contains "HOU to MAD flights"
// 2. Origin is Houston (HOU)
// 3. Destination is Madrid (MAD)
// 4. Dates are May 15 to June 15
// 5. 3 travelers (2 adults + 1 child)
// 6. Flight type is Roundtrip
// 7. Flight search results page is loaded

(() => {
  // Check 1: Page title indicates HOU to MAD flight search
  const pageTitle = document.title;
  const titleHasRoute = pageTitle.includes('HOU') && pageTitle.includes('MAD');

  // Check 2: Verify origin is Houston
  const originInput = document.querySelector('input[name="EGDSSearchFormLocationField-AirportCode-origin_select"]');
  const hasHoustonOrigin = originInput && originInput.value === 'HOU';

  // Check 3: Verify destination is Madrid
  const destInput = document.querySelector('input[name="EGDSSearchFormLocationField-AirportCode-destination_select"]');
  const hasMadridDest = destInput && destInput.value === 'MAD';

  // Check 4: Verify dates - May 15 to June 15
  const startDateInput = document.querySelector('input[name="EGDSDateRangePicker-StartDate-date_form_field"]');
  const endDateInput = document.querySelector('input[name="EGDSDateRangePicker-EndDate-date_form_field"]');
  // Accept any year since test may run in different years
  const hasMay15 = startDateInput && /^\d{4}-05-15$/.test(startDateInput.value);
  const hasJun15 = endDateInput && /^\d{4}-06-15$/.test(endDateInput.value);

  // Check 5: Verify 3 travelers (2 adults + 1 child)
  const adultsInput = document.querySelector('input[name="EGDSSearchFormTravelersField-Adult"]');
  const hasTwo = adultsInput && adultsInput.value === '2';
  // Child age input indicates 1 child is present
  const childAgeInput = document.querySelector('input[name="EGDSSearchFormTravelersField-ChildrenAge-1"]');
  const hasChild = childAgeInput !== null;
  // Also verify the travelers display text
  const travelerBtn = document.querySelector('button.open-traveler-picker-observer-root');
  const has3Travelers = travelerBtn && travelerBtn.textContent.includes('3 travelers');

  // Check 6: Verify roundtrip is selected (active tab)
  const roundtripTab = document.querySelector('li.uitk-tab.active a[href*="ROUND_TRIP"]');
  const isRoundtrip = roundtripTab !== null;

  // Check 7: Flight search results page is loaded (app container exists)
  const flightApp = document.getElementById('app-flights-shopping-pwa');
  const hasFlightApp = flightApp !== null;

  // Check 8: Page ID indicates flight search results page
  const pageIdInput = document.getElementById('pageId');
  const isFlightSearchPage = pageIdInput && pageIdInput.value.includes('Flight-Search-Roundtrip');

  // All conditions must be true
  return titleHasRoute &&
         hasHoustonOrigin &&
         hasMadridDest &&
         hasMay15 &&
         hasJun15 &&
         hasTwo &&
         hasChild &&
         has3Travelers &&
         isRoundtrip &&
         hasFlightApp &&
         isFlightSearchPage;
})()