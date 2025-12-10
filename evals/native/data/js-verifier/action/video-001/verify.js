// Verify video playback has started
// Check if video1 is playing (not paused) or has progressed past 0
// Use IIFE to avoid variable declaration conflicts in repeated executions
(() => {
  const video = document.querySelector('#video1');
  return video && (!video.paused || video.currentTime > 0);
})()