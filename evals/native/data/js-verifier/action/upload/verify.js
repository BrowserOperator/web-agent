// Check if a file has been uploaded to the file input
// The value property contains the fake path (e.g., "C:\fakepath\filename.ext")
(() => {
  const fileInput = document.querySelector('#file-upload');
  return Boolean(fileInput && fileInput.value && fileInput.value.length > 0);
})();
