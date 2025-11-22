// Check if "Bill" was typed in the search filter
// Use unique variable names to avoid conflicts with page's existing JavaScript
(() => {
    const inputElement = document.getElementById('myInput');
    const filterValue = inputElement && inputElement.value ? inputElement.value.trim().toUpperCase() : '';

    // Verify the input contains "Bill"
    const hasFilterValue = filterValue === 'BILL';

    // Check if list items are filtered correctly
    const ulElement = document.getElementById('myUL');
    const listItems = ulElement ? ulElement.getElementsByTagName('li') : [];

    let billyVisible = false;
    let nonMatchingHidden = true;

    for (let i = 0; i < listItems.length; i++) {
        const item = listItems[i];
        const link = item.getElementsByTagName('a')[0];
        const text = link ? link.textContent || link.innerText : '';
        const textUpper = text.toUpperCase();

        const computedStyle = window.getComputedStyle(item);
        const isVisible = computedStyle.display !== 'none';

        // Check if this item should be visible (contains "BILL")
        if (textUpper.indexOf('BILL') > -1) {
            // Billy should be visible
            if (text === 'Billy' && isVisible) {
                billyVisible = true;
            }
        } else {
            // Items without "Bill" should be hidden
            if (isVisible) {
                nonMatchingHidden = false;
            }
        }
    }

    // Return true only if filter is applied and items are correctly filtered
    return hasFilterValue && billyVisible && nonMatchingHidden;
})()