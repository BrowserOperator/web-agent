// Validation: Check if search was performed with "automated testing tools"
// The page title should change from "Search - Microsoft Bing" to "automated testing tools - Search"
// This validates that the search box was filled with the query and the search button was clicked

// Get the page title
document.title.includes('automated testing tools') &&
(document.title.includes(' - Search') || document.title.includes('- Search'))