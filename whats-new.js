(() => {
  const NOTICE = {
    id: "retry-wrong-v1",
    badge: "Mới",
    title: "Làm lại câu sai sau khi tổng kết",
    text: "Xem tổng kết xong, bấm “Làm lại câu sai” để chỉ ôn những câu bạn trả lời sai — không cần làm lại cả đề.",
  };

  const foreverKey = `thvp-notice-hide-${NOTICE.id}`;
  const sessionKey = `thvp-notice-session-${NOTICE.id}`;

  try {
    if (localStorage.getItem(foreverKey) || sessionStorage.getItem(sessionKey)) return;
  } catch {
    return;
  }

  const root = document.createElement("div");
  root.className = "whats-new";
  root.setAttribute("role", "dialog");
  root.setAttribute("aria-label", "Thông báo tính năng mới");
  root.innerHTML = `
    <div class="whats-new-card">
      <div class="whats-new-copy">
        <span class="whats-new-badge">${NOTICE.badge}</span>
        <strong>${NOTICE.title}</strong>
        <p>${NOTICE.text}</p>
      </div>
      <div class="whats-new-actions">
        <button type="button" class="whats-new-btn ghost" data-action="later">Để sau</button>
        <button type="button" class="whats-new-btn primary" data-action="forever">Không hiện lại</button>
      </div>
      <button type="button" class="whats-new-close" data-action="later" aria-label="Đóng">×</button>
    </div>
  `;

  function dismiss(forever) {
    try {
      if (forever) localStorage.setItem(foreverKey, "1");
      else sessionStorage.setItem(sessionKey, "1");
    } catch {}
    root.classList.add("is-out");
    window.setTimeout(() => root.remove(), 220);
  }

  root.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    dismiss(btn.dataset.action === "forever");
  });

  document.body.appendChild(root);
  requestAnimationFrame(() => root.classList.add("is-in"));
})();
