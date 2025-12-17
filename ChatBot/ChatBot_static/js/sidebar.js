function renderSidebar(places) {
  const wrapper = document.getElementById("sidebar-wrapper");
  const sidebar = document.getElementById("sidebar");
  if (!wrapper || !sidebar) return;

  // nếu không có place → đóng sidebar
  if (!Array.isArray(places) || places.length === 0) {
    sidebar.innerHTML = "";
    wrapper.classList.add("hidden");
    return;
  }

    wrapper.classList.remove("hidden");

  sidebar.innerHTML = `
 <div class="w-full h-full bg-gradient-to-b from-gray-900 to-gray-800 text-white p-4 overflow-y-auto">
    <h2 class="text-xl mb-4 flex items-center gap-2">
      <span class="text-blue-400">📍</span> Places
    </h2>

    <div id="placesList" class="flex flex-col gap-4"></div>
  </div>
  `;

  const list = document.getElementById("placesList");

  places.forEach(place => {
    list.insertAdjacentHTML("beforeend", renderPlaceCard(place));
  });
}


function renderPlaceCard(place) {
  const raw = place.filename || "default.jpg";
  const normalized = raw.replace(/\\/g, "/");

  const imageSrc = normalized.includes("://")
    ? normalized
    : `/static/images/${normalized}`;

  return `
    <div class="bg-gray-800 rounded-xl overflow-hidden shadow-lg border border-gray-700 w-full max-w-full box-border">
      <img
        src="${imageSrc}"
        alt="${place.name || 'Place'}"
        class="w-full h-32 object-cover"
        onerror="this.onerror=null; this.src='/static/images/default.jpg';"
      />

      <div class="p-3">
        <h3 class="text-lg font-semibold">${place.name || 'Unknown'}</h3>

        <p class="text-sm text-gray-400">
          📍 ${place.city || 'Unknown'}
        </p>

        ${place.tags ? `
          <p class="text-xs text-gray-500 mt-1">
            🏷 ${place.tags}
          </p>` : ''}

        ${place.rating ? `
          <p class="text-sm mt-1">
            ⭐ ${place.rating}
          </p>` : ''}
      </div>
    </div>
  `;
}
