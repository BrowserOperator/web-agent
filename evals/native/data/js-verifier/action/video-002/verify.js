// Check if video1 has been played (currentTime > 0 indicates it was played)
// The objective was to click the play button for video1
(function() {
  const video1 = document.getElementById('video1');
  return video1 && video1.currentTime > 0;
})()