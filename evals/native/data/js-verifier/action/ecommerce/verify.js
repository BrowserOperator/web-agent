// Validation: Check if "Add to Cart" button was clicked
// Key changes after clicking:
// 1. Header gets 'header-out-of-view' class
// 2. Sticky nav becomes visible (parent changes from sui-hidden to !sui-block)

(() => {
  // Check for header-out-of-view class on header-root
  const headerRoot = document.querySelector('#header-root');
  const hasHeaderClass = headerRoot && headerRoot.classList.contains('header-out-of-view');

  // Check if sticky nav parent container is visible (changed from sui-hidden to !sui-block)
  const stickyNavParent = document.querySelector('#sticky-nav')?.parentElement;
  const isStickyNavVisible = stickyNavParent &&
    !stickyNavParent.classList.contains('sui-hidden') &&
    stickyNavParent.classList.contains('!sui-block');

  // Both indicators should be true for successful Add to Cart
  return hasHeaderClass && isStickyNavVisible;
})()