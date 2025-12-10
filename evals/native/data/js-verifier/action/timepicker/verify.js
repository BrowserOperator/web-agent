// Verify that the time is set to 2:30 PM in any timepicker input
// Using IIFE to avoid variable name collisions with page context
(function() {
  const timepickerInputs = document.querySelectorAll('input.timepicker');
  for (const inp of timepickerInputs) {
    const val = (inp.value || '').toLowerCase().replace(/\s+/g, ' ').trim();
    // Check for 2:30 PM formats
    if (val === '2:30 pm' || val === '02:30 pm' || val === '14:30' || val === '2:30pm' || val === '02:30pm') {
      return true;
    }
  }
  return false;
})()