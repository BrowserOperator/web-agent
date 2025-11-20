// Check if date range has been set to February 1, 2024 - February 28, 2024
// Verify the visible date range text matches
(document.querySelector('#daterange span')?.textContent.trim() === 'February 1, 2024 - February 28, 2024') || false