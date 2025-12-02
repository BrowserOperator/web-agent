// Validation: Check if Google Search was performed for "DevTools automation"
// The search should have been executed and results page loaded
//
// IMPORTANT: Wrapped in IIFE to avoid variable conflicts with page scope

(() => {
  // Check 1: Title should contain the search query
  const title = document.title;
  const titleContainsQuery = title.includes('DevTools automation');

  // Check 2: Title should indicate it's a search results page
  const titleIndicatesSearch = title.includes('Google Search') || title.includes(' - Google');

  // Check 3: URL should contain search parameters
  const urlContainsSearch = window.location.search.includes('q=') || window.location.pathname.includes('/search');

  // Check 4: Schema should be SearchResultsPage (if available)
  const htmlElement = document.documentElement;
  const schemaCheck = htmlElement.getAttribute('itemtype') === 'http://schema.org/SearchResultsPage';

  // Combine checks - at minimum title should contain query and indicate search
  return titleContainsQuery && titleIndicatesSearch && (urlContainsSearch || schemaCheck);
})()