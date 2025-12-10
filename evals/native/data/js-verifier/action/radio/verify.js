// Verify that the "Medium" pizza size radio button is checked
(() => {
  const mediumRadio = document.querySelector('input[type="radio"][name="size"][value="medium"]');
  return mediumRadio && mediumRadio.checked;
})()