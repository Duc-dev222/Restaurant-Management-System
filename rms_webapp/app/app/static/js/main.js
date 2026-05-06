function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  if (sidebar) {
    sidebar.classList.toggle("open");
  }
}

document.addEventListener("click", (event) => {
  const sidebar = document.getElementById("sidebar");
  if (!sidebar || window.innerWidth > 900) {
    return;
  }

  const toggle = document.querySelector(".menu-toggle");
  const clickedInsideSidebar = sidebar.contains(event.target);
  const clickedToggle = toggle && toggle.contains(event.target);

  if (!clickedInsideSidebar && !clickedToggle) {
    sidebar.classList.remove("open");
  }
});

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-flash]").forEach((flash) => {
    window.setTimeout(() => {
      flash.remove();
    }, 5000);
  });

  document.querySelectorAll("[data-collapsible-list]").forEach((list) => {
    const panel = list.closest(".panel");
    const toggle = panel ? panel.querySelector("[data-list-toggle]") : null;
    const visibleCount = Number(list.dataset.visibleCount || 12);
    const rows = list.querySelectorAll("tbody tr");

    if (!toggle || rows.length <= visibleCount) {
      if (toggle) {
        toggle.hidden = true;
      }
      return;
    }

    const updateLabel = () => {
      toggle.textContent = list.classList.contains("is-collapsed")
        ? `Xem tất cả ${rows.length} dòng`
        : "Thu gọn danh sách";
    };

    updateLabel();
    toggle.addEventListener("click", () => {
      list.classList.toggle("is-collapsed");
      updateLabel();
    });
  });
});
