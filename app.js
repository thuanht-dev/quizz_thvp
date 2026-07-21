(() => {
  const params = new URLSearchParams(location.search);
  const mode = params.get("mode");
  const moduleId = Number(params.get("module") || "0");
  const data = window.QUIZ_DATA;
  const $ = (id) => document.getElementById(id);

  if (!data?.modules?.length) {
    showError("Không tải được dữ liệu quiz.");
    return;
  }

  const isMixed = mode === "mixed";
  let mod;
  let questions;
  let storageKey;
  let sessionIds = null;

  if (isMixed) {
    const mixed = data.mixed;
    if (!mixed?.questions?.length) {
      showError('Chưa có ngân hàng tổng hợp. <a href="home.html">Về trang chủ</a>');
      return;
    }
    mod = {
      id: "mixed",
      short: mixed.short || "Tổng hợp",
      title: mixed.title || "Ôn trắc nghiệm tổng hợp",
    };
    storageKey = "thvp-quiz-mixed";
    const prepared = prepareMixedSession(mixed);
    questions = prepared.questions;
    sessionIds = prepared.ids;
  } else {
    mod = data.modules.find((m) => m.id === moduleId);
    if (!mod) {
      showError('Không tìm thấy module. <a href="home.html">Về trang chủ</a>');
      return;
    }
    storageKey = `thvp-quiz-m${moduleId}`;
    questions = mod.questions;
  }

  let answers = Object.create(null);
  let index = 0;
  let jumpFilter = "all";
  let reviewRows = [];
  let menuOpen = false;

  document.title = `THVP Quiz – ${mod.short}`;
  $("module-eyebrow").textContent = mod.short;
  setupSlides(isMixed ? null : moduleId);
  restoreProgress();
  $("quiz-view").classList.remove("hidden");

  if (isMixed) {
    const resetBtn = $("btn-reset");
    if (resetBtn) resetBtn.textContent = "Làm đề mới (50 câu khác)";
  }

  $("btn-prev").addEventListener("click", () => go(-1));
  $("btn-next").addEventListener("click", () => {
    if (index >= questions.length - 1) showResults();
    else go(1);
  });
  $("btn-submit").addEventListener("click", () => {
    closeMenu();
    const n = Object.keys(answers).length;
    if (n < questions.length && !confirm(`Đã làm ${n}/${questions.length} câu. Xem tổng kết?`)) return;
    showResults();
  });
  $("btn-retry").addEventListener("click", () => {
    const msg = isMixed
      ? "Xóa kết quả và rút 50 câu ngẫu nhiên mới?"
      : "Xóa tiến độ và làm lại?";
    if (!confirm(msg)) return;
    clearProgress();
    location.reload();
  });
  $("btn-reset").addEventListener("click", () => {
    closeMenu();
    const msg = isMixed
      ? "Xóa tiến độ và rút bộ 50 câu mới?"
      : "Xóa tiến độ module này?";
    if (!confirm(msg)) return;
    clearProgress();
    location.reload();
  });
  $("btn-menu").addEventListener("click", (e) => {
    e.stopPropagation();
    menuOpen = !menuOpen;
    $("qz-menu").classList.toggle("hidden", !menuOpen);
    $("btn-menu").setAttribute("aria-expanded", String(menuOpen));
  });
  document.addEventListener("click", () => closeMenu());
  $("qz-menu").addEventListener("click", (e) => e.stopPropagation());

  $("btn-map").addEventListener("click", () => openMap(true));
  $("btn-close-map").addEventListener("click", () => openMap(false));
  $("map-backdrop").addEventListener("click", () => openMap(false));

  $("btn-filter-jump").addEventListener("click", () => {
    jumpFilter = jumpFilter === "all" ? "wrong" : jumpFilter === "wrong" ? "todo" : "all";
    $("btn-filter-jump").textContent =
      { all: "Tất cả", wrong: "Chỉ sai", todo: "Chưa làm" }[jumpFilter];
    buildJump();
  });

  $("btn-review-wrong").addEventListener("click", () => {
    setReviewFilter("wrong");
    $("review-wrap").scrollIntoView({ behavior: "smooth" });
  });

  document.querySelectorAll(".review-filters .qz-chip").forEach((chip) => {
    chip.addEventListener("click", () => setReviewFilter(chip.dataset.filter));
  });

  document.addEventListener("keydown", onKey);
  renderQuestion();

  function prepareMixedSession(mixed) {
    const draw = Number(mixed.drawCount) || 50;
    const plan = mixed.drawPlan || { basics: 18, files: 10, security: 8, office: 14 };
    let saved = null;
    try {
      saved = JSON.parse(localStorage.getItem(storageKey) || "null");
    } catch {}

    if (saved?.ids?.length) {
      const byId = Object.fromEntries(mixed.questions.map((q) => [q.id, q]));
      const restored = saved.ids.map((id) => byId[id]).filter(Boolean);
      if (restored.length === saved.ids.length && restored.length > 0) {
        return {
          ids: saved.ids,
          questions: renumber(restored),
        };
      }
    }

    const drawn = drawBalanced(mixed.questions, plan, draw);
    const ids = drawn.map((q) => q.id);
    return { ids, questions: renumber(drawn) };
  }

  function drawBalanced(pool, plan, total) {
    const byTopic = {};
    for (const q of pool) {
      const t = q.topic || "basics";
      (byTopic[t] ||= []).push(q);
    }
    for (const list of Object.values(byTopic)) shuffleInPlace(list);

    const picked = [];
    const used = new Set();
    for (const [topic, n] of Object.entries(plan)) {
      const list = byTopic[topic] || [];
      let take = Math.min(n, list.length);
      for (let i = 0; i < take; i++) {
        picked.push(list[i]);
        used.add(list[i].id);
      }
    }

    if (picked.length < total) {
      const rest = pool.filter((q) => !used.has(q.id));
      shuffleInPlace(rest);
      for (const q of rest) {
        if (picked.length >= total) break;
        picked.push(q);
      }
    }

    shuffleInPlace(picked);
    return picked.slice(0, total);
  }

  function renumber(list) {
    return list.map((q, i) => ({
      ...q,
      poolId: q.id,
      id: i + 1,
    }));
  }

  function shuffleInPlace(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }

  function closeMenu() {
    menuOpen = false;
    $("qz-menu")?.classList.add("hidden");
    $("btn-menu")?.setAttribute("aria-expanded", "false");
  }

  function openMap(on) {
    $("qz-map").classList.toggle("hidden", !on);
    $("qz-map").setAttribute("aria-hidden", String(!on));
    if (on) {
      closeMenu();
      buildJump();
    }
  }

  function onKey(e) {
    if (!$("result-view").classList.contains("hidden")) return;
    if (e.target.matches("input, textarea, select")) return;
    if (!$("qz-map").classList.contains("hidden") && e.key === "Escape") {
      openMap(false);
      return;
    }
    const key = e.key.toUpperCase();
    const q = questions[index];
    const revealed = Boolean(answers[q.id]);

    if (!revealed && ["A", "B", "C", "D"].includes(key)) {
      e.preventDefault();
      selectAnswer(key);
      return;
    }
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      go(-1);
    } else if (e.key === "ArrowRight" || (e.key === "Enter" && revealed)) {
      e.preventDefault();
      if (index >= questions.length - 1 && revealed) showResults();
      else if (e.key === "ArrowRight" || revealed) go(1);
    }
  }

  function go(delta) {
    const next = index + delta;
    if (next < 0 || next >= questions.length) return;
    index = next;
    saveProgress();
    renderQuestion({ scrollTop: true });
  }

  function selectAnswer(key) {
    const q = questions[index];
    if (answers[q.id]) return;
    answers[q.id] = key;
    saveProgress();
    renderQuestion({ focusFeedback: true });
  }

  function showError(msg) {
    const el = $("error");
    el.classList.remove("hidden");
    el.innerHTML = msg;
  }

  function renderQuestion(opts = {}) {
    const q = questions[index];
    const selected = answers[q.id] || null;
    const revealed = Boolean(selected);
    const { correct, wrong } = tally();
    const done = Object.keys(answers).length;
    const pct = Math.round((done / questions.length) * 100);

    $("q-label").textContent = `Câu ${q.id}`;
    $("q-text").textContent = q.text;
    $("progress-text").textContent = `${index + 1}/${questions.length}`;
    $("score-live").textContent = `${correct} đúng · ${wrong} sai`;
    $("progress-fill").style.width = `${pct}%`;
    document.querySelector(".qz-bar")?.setAttribute("aria-valuenow", String(pct));
    $("btn-prev").disabled = index === 0;
    $("btn-next").textContent = index >= questions.length - 1 ? "Tổng kết" : "Tiếp";
    $("btn-next").classList.toggle("ready", revealed);

    $("options").innerHTML = ["A", "B", "C", "D"]
      .map((key) => {
        let cls = "qz-choice";
        if (revealed) {
          if (key === q.answer) cls += " is-correct";
          else if (selected === key) cls += " is-wrong";
          else cls += " is-dim";
        }
        return `<button type="button" class="${cls}" data-key="${key}" role="option" ${revealed ? "disabled" : ""}>
          <span class="letter">${key}</span>
          <span class="body">${escapeHtml(q.options[key])}</span>
        </button>`;
      })
      .join("");

    if (!revealed) {
      $("options").querySelectorAll(".qz-choice").forEach((btn) => {
        btn.addEventListener("click", () => selectAnswer(btn.dataset.key));
      });
    }

    renderFeedback(q, selected);

    if (opts.scrollTop) {
      const sc = $("qz-scroll");
      if (sc) sc.scrollTop = 0;
    }
    if (opts.focusFeedback) {
      requestAnimationFrame(() => {
        const fb = $("instant-feedback");
        if (fb && !fb.classList.contains("hidden")) {
          fb.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
      });
    }
    if (!$("qz-map").classList.contains("hidden")) buildJump();
  }

  function renderFeedback(q, selected) {
    const box = $("instant-feedback");
    if (!selected) {
      box.className = "qz-fb hidden";
      box.innerHTML = "";
      return;
    }

    const ok = selected === q.answer;
    box.className = `qz-fb ${ok ? "ok" : "bad"}`;
    box.innerHTML = `
      <p class="fb-title">${ok ? "Chính xác" : "Chưa đúng"}</p>
      ${
        ok
          ? ""
          : `<p class="fb-line">Đáp án đúng: <strong>${q.answer}. ${escapeHtml(q.options[q.answer])}</strong></p>`
      }
      ${explainHtml(q)}
    `;
  }

  function explainHtml(q) {
    const icon = (q.icon || "💡").trim();
    const summary = escapeHtml(
      (q.explain || "").trim() || "Xem lại kiến thức lý thuyết liên quan."
    );
    const detail = (q.detail || "").trim();
    return `
      <div class="fb-explain">
        <span class="fb-icon" aria-hidden="true">${escapeHtml(icon)}</span>
        <div class="fb-explain-body">
          <p class="fb-summary">${summary}</p>
          ${
            detail
              ? `<details class="fb-detail">
                  <summary>Chi tiết</summary>
                  <p>${escapeHtml(detail)}</p>
                </details>`
              : ""
          }
        </div>
      </div>
    `;
  }

  function buildJump() {
    const jump = $("jump");
    const items = questions
      .map((q, i) => ({ q, i }))
      .filter(({ q }) => {
        const a = answers[q.id];
        if (jumpFilter === "wrong") return a && a !== q.answer;
        if (jumpFilter === "todo") return !a;
        return true;
      });

    if (!items.length) {
      jump.innerHTML = `<p class="empty">Không có câu trong bộ lọc này.</p>`;
      return;
    }

    jump.innerHTML = items
      .map(({ q, i }) => {
        const a = answers[q.id];
        const cls = [
          "dot",
          i === index ? "current" : "",
          a && a === q.answer ? "ok" : "",
          a && a !== q.answer ? "bad" : "",
        ]
          .filter(Boolean)
          .join(" ");
        return `<button type="button" class="${cls}" data-i="${i}">${q.id}</button>`;
      })
      .join("");

    jump.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => {
        index = Number(btn.dataset.i);
        openMap(false);
        saveProgress();
        renderQuestion({ scrollTop: true });
      });
    });
  }

  function tally() {
    let correct = 0;
    let wrong = 0;
    for (const q of questions) {
      const a = answers[q.id];
      if (!a) continue;
      if (a === q.answer) correct += 1;
      else wrong += 1;
    }
    return { correct, wrong };
  }

  function gradeLabel(pct) {
    if (pct >= 90) return "Xuất sắc";
    if (pct >= 80) return "Giỏi";
    if (pct >= 65) return "Khá";
    if (pct >= 50) return "Trung bình";
    return "Cần ôn thêm";
  }

  function showResults() {
    let correct = 0;
    let wrong = 0;
    let skip = 0;

    reviewRows = questions.map((q) => {
      const user = answers[q.id] || null;
      const ok = user === q.answer;
      if (!user) skip += 1;
      else if (ok) correct += 1;
      else wrong += 1;
      return { q, user, ok, status: !user ? "skip" : ok ? "correct" : "wrong" };
    });

    const pct = Math.round((correct / questions.length) * 100);
    $("quiz-view").classList.add("hidden");
    $("result-view").classList.remove("hidden");
    document.body.classList.add("showing-result");
    document.removeEventListener("keydown", onKey);
    openMap(false);
    closeMenu();

    $("result-title").textContent = `${mod.short}: ${mod.title}`;
    $("score-pct").textContent = `${pct}%`;
    $("score-ring").style.setProperty("--pct", String(pct));
    $("score-grade").textContent = gradeLabel(pct);
    $("score-summary").textContent = `Đúng ${correct}/${questions.length} · Sai ${wrong} · Chưa làm ${skip}`;
    $("stat-correct").textContent = String(correct);
    $("stat-wrong").textContent = String(wrong);
    $("stat-skip").textContent = String(skip);
    setReviewFilter("all");
    window.scrollTo({ top: 0 });
  }

  function setReviewFilter(filter) {
    document.querySelectorAll(".review-filters .qz-chip").forEach((c) => {
      c.classList.toggle("active", c.dataset.filter === filter);
    });

    const filtered = reviewRows.filter((r) => {
      if (filter === "all") return true;
      return r.status === filter;
    });

    $("review-list").innerHTML = filtered.length
      ? filtered
          .map(({ q, user, ok, status }) => {
            const badge =
              status === "skip"
                ? `<span class="qz-badge bad">Chưa làm</span>`
                : ok
                  ? `<span class="qz-badge ok">Đúng</span>`
                  : `<span class="qz-badge bad">Sai</span>`;
            return `<article class="qz-review ${status === "correct" ? "correct" : "wrong"}">
              ${badge}
              <h3>Câu ${q.id}. ${escapeHtml(q.text)}</h3>
              <p class="line">Bạn chọn: <strong>${user ? user + ". " + escapeHtml(q.options[user]) : "—"}</strong></p>
              <p class="line">Đáp án đúng: <strong>${q.answer}. ${escapeHtml(q.options[q.answer])}</strong></p>
              ${explainHtml(q)}
            </article>`;
          })
          .join("")
      : `<p class="empty">Không có câu nào trong bộ lọc này.</p>`;
  }

  function setupSlides(mid) {
    const link = $("link-slides");
    if (!link) return;
    if (mid == null || !window.LEARN_PATH) {
      link.classList.add("hidden");
      return;
    }
    const unit = window.LEARN_PATH.units.find((u) => u.modules.some((m) => m.id === mid));
    if (!unit?.slides) {
      link.classList.add("hidden");
      return;
    }
    link.classList.remove("hidden");
    link.href = unit.slides.url;
  }

  function saveProgress() {
    try {
      const payload = { answers, index, ts: Date.now() };
      if (isMixed && sessionIds) payload.ids = sessionIds;
      localStorage.setItem(storageKey, JSON.stringify(payload));
    } catch {}
  }

  function restoreProgress() {
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) {
        if (isMixed) saveProgress();
        return;
      }
      const saved = JSON.parse(raw);
      if (saved?.answers) answers = saved.answers;
      if (Number.isInteger(saved?.index) && saved.index >= 0 && saved.index < questions.length) {
        index = saved.index;
      }
      if (isMixed && !saved?.ids) saveProgress();
    } catch {}
  }

  function clearProgress() {
    try {
      localStorage.removeItem(storageKey);
    } catch {}
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
})();
