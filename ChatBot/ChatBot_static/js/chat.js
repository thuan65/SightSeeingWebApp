// ví dụ khi bot trả place
function onBotFoundPlace(place) {
  renderSidebar(place.name, place.image);

  // mở sidebar nếu có
  document
    .getElementById("sidebar-wrapper")
    .classList.remove("hidden");
}

renderSidebar(
  "Paris",
  "https://images.unsplash.com/photo-1502602898657-3e91760cbb34"
);
