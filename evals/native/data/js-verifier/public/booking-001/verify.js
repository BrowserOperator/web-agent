// Validation for: Find hotels in Porto (Portugal) for dates August 10 to August 17 for 2 adults
// Checks:
// 1. Body has id 'b2searchresultsPage' (search results page)
// 2. Title contains 'porto' but NOT 'porto alegre' (must be Porto, Portugal - not Porto Alegre, Brazil)
// 3. Page shows 'Aug 10' and 'Aug 17' (date range)
// 4. Page shows '2 adults' (guest count)

(() => {
  const titleLower = document.title.toLowerCase();
  // Must be Porto, Portugal - exclude Brazilian cities and similar names
  // - Porto Alegre (Brazil)
  // - Porto De Galinhas (Brazil)
  // - Portofino (Italy)
  const isPortoPortugal = titleLower.includes('porto') &&
    !titleLower.includes('porto alegre') &&
    !titleLower.includes('porto de galinhas') &&
    !titleLower.includes('portofino');

  return document.body.id === 'b2searchresultsPage' &&
    isPortoPortugal &&
    document.body.innerText.includes('Aug 10') &&
    document.body.innerText.includes('Aug 17') &&
    document.body.innerText.includes('2 adults');
})()