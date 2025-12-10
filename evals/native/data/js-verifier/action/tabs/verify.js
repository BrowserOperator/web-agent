// Verify that the "Proin dolor" tab (tabs-2) is the currently active tab
// The demo is inside an iframe at https://jqueryui.com/resources/demos/tabs/default.html
// jQuery UI tabs mark the active tab's parent li with ui-tabs-active and ui-state-active classes

(() => {
  // Get the iframe containing the tabs demo
  const iframe = document.querySelector('iframe');
  if (!iframe) return false;

  const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
  if (!iframeDoc) return false;

  // Find the "Proin dolor" tab link (it links to #tabs-2)
  const proinDolorLinks = Array.from(iframeDoc.querySelectorAll('a')).filter(a => a.textContent.trim() === 'Proin dolor');
  if (proinDolorLinks.length === 0) return false;

  const proinDolorTab = proinDolorLinks[0];
  const tabLi = proinDolorTab.closest('li');
  if (!tabLi) return false;

  // Check if the tab is active (has ui-tabs-active class)
  const tabIsActive = tabLi.classList.contains('ui-tabs-active') || tabLi.classList.contains('ui-state-active');

  return tabIsActive;
})()