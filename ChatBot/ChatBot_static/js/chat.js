function toggleSidebar() {
  const wrapper = document.getElementById("sidebar-wrapper");
  wrapper.classList.toggle("hidden");
  
  document.body.classList.toggle(
    "sidebar-open",
    !wrapper.classList.contains("hidden")
  );
}
