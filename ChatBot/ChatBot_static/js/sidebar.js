function renderSidebar(placeName, placeImage) {
  const sidebar = document.getElementById("sidebar");
  if (!sidebar) return;
  sidebar.innerHTML = `
    <div class="w-80 bg-gradient-to-b from-gray-900 to-gray-800 text-white p-6 flex flex-col h-screen">
      <div class="flex items-center gap-2 mb-6">
        <span class="text-blue-400 text-xl">📍</span>
        <h2 class="text-xl">Place Explorer</h2>
      </div>

      ${
        placeName && placeImage
          ? `
          <div class="flex-1 flex flex-col gap-4">
            <div class="relative rounded-xl overflow-hidden shadow-2xl">
              <img
                src="${placeImage}"
                alt="${placeName}"
                class="w-full h-64 object-cover"
              />
              <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
                <h3 class="text-xl">${placeName}</h3>
              </div>
            </div>

            <div class="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
              <p class="text-gray-300 text-sm">
                Currently viewing:
                <span class="text-white">${placeName}</span>
              </p>
            </div>
          </div>
        `
          : `
          <div class="flex-1 flex items-center justify-center">
            <div class="text-center text-gray-400">
              <div class="text-6xl mb-4 opacity-20">📍</div>
              <p>Ask about any place to see</p>
              <p>beautiful photos here!</p>
              <p class="text-xs mt-4 text-gray-500">
                Try: "Tell me about Paris" or "Show me Tokyo"
              </p>
            </div>
          </div>
        `
      }
    </div>
  `;
}

