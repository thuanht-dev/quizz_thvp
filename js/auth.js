(() => {
  const api = () => window.THVP_API;

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function ensureStyles() {
    if (document.getElementById("thvp-auth-styles")) return;
    const style = document.createElement("style");
    style.id = "thvp-auth-styles";
    style.textContent = `
      .auth-gate {
        position: fixed; inset: 0; z-index: 200;
        display: grid; place-items: center;
        padding: 1rem;
        background: rgba(18, 26, 43, 0.45);
        backdrop-filter: blur(4px);
      }
      .auth-card {
        width: min(420px, 100%);
        background: #fff;
        border: 1px solid #d7deea;
        border-radius: 16px;
        padding: 1.35rem 1.25rem 1.2rem;
        box-shadow: 0 16px 48px rgba(18,26,43,.16);
      }
      .auth-card h2 {
        margin: 0 0 0.35rem;
        font-family: Sora, Be Vietnam Pro, system-ui, sans-serif;
        font-size: 1.25rem;
        letter-spacing: -0.03em;
      }
      .auth-card .auth-lead {
        margin: 0 0 1rem;
        color: #5d6b81;
        font-size: 0.9rem;
        line-height: 1.45;
      }
      .auth-card label {
        display: block;
        font-size: 0.78rem;
        font-weight: 700;
        color: #5d6b81;
        margin: 0.65rem 0 0.3rem;
      }
      .auth-card input {
        width: 100%;
        box-sizing: border-box;
        border: 1.5px solid #d7deea;
        border-radius: 10px;
        padding: 0.7rem 0.8rem;
        font: inherit;
        font-size: 0.95rem;
      }
      .auth-card input:focus {
        outline: 2px solid #0c6f7c;
        outline-offset: 1px;
      }
      .auth-error {
        margin: 0.75rem 0 0;
        color: #b42318;
        font-size: 0.88rem;
        font-weight: 600;
      }
      .auth-actions {
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
      }
      .auth-actions button {
        flex: 1;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        font: inherit;
        font-weight: 700;
        cursor: pointer;
        background: #0c6f7c;
        color: #fff;
      }
      .auth-actions button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      .auth-skip {
        display: block;
        width: 100%;
        margin-top: 0.55rem;
        border: none;
        background: transparent;
        color: #5d6b81;
        font: inherit;
        font-size: 0.82rem;
        font-weight: 600;
        cursor: pointer;
        text-align: center;
      }
      .auth-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        font-size: 0.82rem;
        font-weight: 600;
        color: #08545e;
        background: #d7f0f3;
        border-radius: 999px;
        padding: 0.35rem 0.55rem 0.35rem 0.7rem;
      }
      .auth-chip button {
        border: none;
        background: transparent;
        color: #08545e;
        font: inherit;
        font-size: 0.78rem;
        font-weight: 700;
        cursor: pointer;
        padding: 0 0.25rem;
      }
      .auth-warn {
        margin: 0 0 1rem;
        padding: 0.75rem 0.9rem;
        border-radius: 12px;
        background: #fff8e8;
        border: 1px solid #f0d9a0;
        color: #7a5a12;
        font-size: 0.88rem;
      }
    `;
    document.head.appendChild(style);
  }

  function mountUserChip(targetSelector) {
    const a = api();
    const student = a?.getStudent?.();
    const host = document.querySelector(targetSelector);
    if (!host) return false;

    let slot = host.querySelector(".auth-user-slot");
    if (!slot) {
      slot = document.createElement("div");
      slot.className = "auth-user-slot";
      host.appendChild(slot);
    }

    if (!student) {
      slot.innerHTML = `<button type="button" class="home-link" id="btn-open-login">Đăng nhập</button>`;
      slot.querySelector("#btn-open-login")?.addEventListener("click", () => showLogin({ force: true }));
      return true;
    }

    slot.innerHTML = `
      <span class="auth-chip" title="${escapeHtml(student.code)}">
        ${escapeHtml(student.name)}
        <button type="button" id="btn-logout">Thoát</button>
      </span>`;
    slot.querySelector("#btn-logout")?.addEventListener("click", () => {
      a.logout();
      location.reload();
    });
    return true;
  }

  function showLogin({ force = false, gateQuiz = false } = {}) {
    ensureStyles();
    const a = api();
    if (a?.getStudent?.() && !force) return Promise.resolve(a.getStudent());

    if (!a?.configured?.()) {
      if (gateQuiz) {
        return showConfigMissing(gateQuiz);
      }
      return Promise.resolve(null);
    }

    return new Promise((resolve) => {
      const existing = document.querySelector(".auth-gate");
      if (existing) existing.remove();

      const gate = document.createElement("div");
      gate.className = "auth-gate";
      gate.innerHTML = `
        <form class="auth-card" id="auth-form">
          <h2>Đăng nhập học viên</h2>
          <p class="auth-lead">Nhập mã và họ tên để lưu tiến độ, điểm và lịch sử làm bài.</p>
          <label for="auth-code">Mã học viên</label>
          <input id="auth-code" name="code" autocomplete="username" required maxlength="32" placeholder="VD: SV001" />
          <label for="auth-name">Họ và tên</label>
          <input id="auth-name" name="name" autocomplete="name" required maxlength="80" placeholder="Nguyễn Văn A" />
          <p class="auth-error hidden" id="auth-error"></p>
          <div class="auth-actions">
            <button type="submit" id="auth-submit">Vào học</button>
          </div>
          ${gateQuiz ? "" : '<button type="button" class="auth-skip" id="auth-skip">Bỏ qua (chỉ học trên máy này)</button>'}
        </form>`;
      document.body.appendChild(gate);

      const errEl = gate.querySelector("#auth-error");
      const form = gate.querySelector("#auth-form");

      gate.querySelector("#auth-skip")?.addEventListener("click", () => {
        gate.remove();
        resolve(null);
      });

      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const code = form.code.value;
        const name = form.name.value;
        const btn = gate.querySelector("#auth-submit");
        btn.disabled = true;
        errEl.classList.add("hidden");
        try {
          const student = await a.login(code, name);
          a.startHeartbeat?.();
          gate.remove();
          mountUserChip(".home-bar-actions") || mountUserChip(".home-bar");
          resolve(student);
        } catch (err) {
          errEl.textContent = err.message || "Đăng nhập thất bại.";
          errEl.classList.remove("hidden");
          btn.disabled = false;
        }
      });

      form.code.focus();
    });
  }

  function showConfigMissing(gateQuiz) {
    ensureStyles();
    return new Promise((resolve) => {
      const gate = document.createElement("div");
      gate.className = "auth-gate";
      gate.innerHTML = `
        <div class="auth-card">
          <h2>Chưa kết nối backend</h2>
          <p class="auth-warn">
            Điền <code>url</code> và <code>anonKey</code> trong <code>js/config.js</code>,
            rồi chạy SQL trong <code>supabase/schema.sql</code>. Xem <code>docs/HUONG_DAN_BACKEND.md</code>.
          </p>
          <div class="auth-actions">
            <button type="button" id="auth-continue">${gateQuiz ? "Vào quiz offline" : "Đóng"}</button>
          </div>
        </div>`;
      document.body.appendChild(gate);
      gate.querySelector("#auth-continue").addEventListener("click", () => {
        gate.remove();
        resolve(null);
      });
    });
  }

  async function requireLoginForQuiz() {
    const a = api();
    if (a?.getStudent?.()) {
      a.startHeartbeat?.();
      return a.getStudent();
    }
    // Quiz: bắt buộc login nếu đã cấu hình; nếu chưa config thì cho offline
    if (a?.configured?.()) {
      return showLogin({ force: true, gateQuiz: true });
    }
    await showConfigMissing(true);
    return null;
  }

  function bootHome() {
    ensureStyles();
    mountUserChip(".home-bar-actions") || mountUserChip(".home-bar");
    const a = api();
    if (a?.configured?.() && !a.getStudent?.()) {
      try {
        if (!sessionStorage.getItem("thvp-login-prompted")) {
          sessionStorage.setItem("thvp-login-prompted", "1");
          showLogin({ force: false });
        }
      } catch {
        showLogin({ force: false });
      }
    } else if (a?.getStudent?.()) {
      a.startHeartbeat?.();
    }
  }

  window.THVP_AUTH = {
    showLogin,
    requireLoginForQuiz,
    mountUserChip,
    bootHome,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      if (document.body?.dataset?.authBoot === "home") bootHome();
    });
  } else if (document.body?.dataset?.authBoot === "home") {
    bootHome();
  }
})();
