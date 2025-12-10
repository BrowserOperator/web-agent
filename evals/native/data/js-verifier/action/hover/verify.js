// Check if the first figcaption is visible (indicating hover was successful)
// The figcaption should be visible when hovering over the avatar
(() => {
  const figure = document.querySelector('.figure');
  const figcaption = figure ? figure.querySelector('.figcaption') : null;

  if (!figcaption) {
    return false;
  }

  const styles = window.getComputedStyle(figcaption);
  const isVisible = styles.display !== 'none' &&
                    styles.visibility !== 'hidden' &&
                    styles.opacity !== '0' &&
                    parseFloat(styles.opacity) > 0;
  return isVisible;
})()