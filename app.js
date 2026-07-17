(() => {
  const params = new URLSearchParams(location.search);
  const moduleId = Number(params.get("module") || "0");
  const data = window.QUIZ_DATA;

  const $ = (id) => document.getElementById(id);
  const errorEl = $("error");
  const quizView = $("quiz-view");
  const resultView = $("result-view");

  if (!data?.modules?.length) {
    showError("Không tải được dữ liệu quiz-data.js");
    return;
  }

  const mod = data.modules.find((m) => m.id === moduleId);
  if (!mod) {
    showError("Không tìm thấy module. Quay lại trang chủ để chọn module.");
    return;
  }

  document.title = `THVP Quiz – ${mod.short}`;
  $("module-eyebrow").textContent = mod.short;
  $("module-title").textContent = mod.title;
  fillSlideBanner(moduleId);

  const questions = mod.questions;
  const answers = Object.create(null);
  let index = 0;

  quizView.classList.remove("hidden");

  $("btn-prev").addEventListener("click", () => {
    if (index > 0) {
      index -= 1;
      renderQuestion();
    }
  });

  $("btn-next").addEventListener("click", () => {
    if (index < questions.length - 1) {
      index += 1;
      renderQuestion();
    }
  });

  $("btn-submit").addEventListener("click", () => {
    const answered = Object.keys(answers).length;
    const msg =
      answered < questions.length
        ? `Bạn mới trả lời ${answered}/${questions.length} câu. Xem tổng kết ngay?`
        : "Xem tổng kết toàn module?";
    if (confirm(msg)) showResults();
  });

  $("btn-retry").addEventListener("click", () => location.reload());

  $("btn-review").addEventListener("click", () => {
    $("review-wrap").classList.remove("hidden");
    $("review-wrap").scrollIntoView({ behavior: "smooth", block: "start" });
  });

  renderQuestion();

  function showError(msg) {
    errorEl.classList.remove("hidden");
    errorEl.innerHTML = `<p>${msg}</p><p><a class="btn btn-primary" href="index.html">Về trang chủ</a></p>`;
  }

  function renderQuestion() {
    const q = questions[index];
    const selected = answers[q.id] || null;
    const revealed = Boolean(selected);

    $("q-label").textContent = `Câu ${q.id}`;
    $("q-text").textContent = q.text;
    $("progress-text").textContent = `Câu ${index + 1} / ${questions.length}`;
    $("answered-text").textContent = `Đã trả lời: ${Object.keys(answers).length}`;
    $("progress-fill").style.width = `${((index + 1) / questions.length) * 100}%`;
    $("btn-prev").disabled = index === 0;
    $("btn-next").disabled = index === questions.length - 1;

    $("options").innerHTML = ["A", "B", "C", "D"]
      .map((key) => {
        let cls = "option";
        if (revealed) {
          if (key === q.answer) cls += " is-correct";
          if (selected === key && key !== q.answer) cls += " is-wrong";
          if (selected === key) cls += " selected";
        }
        return `<button type="button" class="${cls}" data-key="${key}" ${revealed ? "disabled" : ""}>
          <span class="key">${key}</span>
          <span>${escapeHtml(q.options[key])}</span>
        </button>`;
      })
      .join("");

    if (!revealed) {
      $("options").querySelectorAll(".option").forEach((btn) => {
        btn.addEventListener("click", () => {
          answers[q.id] = btn.dataset.key;
          renderQuestion();
        });
      });
    }

    renderFeedback(q, selected);
    buildJump();
  }

  function renderFeedback(q, selected) {
    const box = $("instant-feedback");
    if (!selected) {
      box.classList.add("hidden");
      box.innerHTML = "";
      return;
    }

    const ok = selected === q.answer;
    const knowledge = (q.explain || "").trim();

    box.classList.remove("hidden");
    box.className = `instant-feedback ${ok ? "ok" : "bad"}`;
    box.innerHTML = `
      <div class="fb-head">${ok ? "Chính xác" : "Chưa đúng"}</div>
      <p class="fb-line"><strong>Bạn chọn:</strong> ${selected}. ${escapeHtml(q.options[selected])}</p>
      <p class="fb-line"><strong>Đáp án đúng:</strong> ${q.answer}. ${escapeHtml(q.options[q.answer])}</p>
      <div class="knowledge">
        <b>Giải thích / kiến thức</b>
        ${escapeHtml(knowledge)}
      </div>
      <div class="fb-actions">
        ${
          index < questions.length - 1
            ? `<button type="button" class="btn btn-primary" id="btn-go-next">Câu tiếp theo →</button>`
            : `<button type="button" class="btn btn-primary" id="btn-go-summary">Xem tổng kết module</button>`
        }
      </div>
    `;

    const nextBtn = $("btn-go-next");
    if (nextBtn) {
      nextBtn.addEventListener("click", () => {
        index += 1;
        renderQuestion();
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    }
    const sumBtn = $("btn-go-summary");
    if (sumBtn) sumBtn.addEventListener("click", showResults);
  }

  function buildJump() {
    const jump = $("jump");
    jump.innerHTML = questions
      .map((q, i) => {
        const cls = ["dot", answers[q.id] ? "answered" : "", i === index ? "current" : ""]
          .filter(Boolean)
          .join(" ");
        const mark =
          answers[q.id] && answers[q.id] === q.answer
            ? " ok-dot"
            : answers[q.id]
              ? " bad-dot"
              : "";
        return `<button type="button" class="${cls}${mark}" data-i="${i}" title="Câu ${q.id}">${q.id}</button>`;
      })
      .join("");

    jump.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => {
        index = Number(btn.dataset.i);
        renderQuestion();
      });
    });
  }

  function showResults() {
    let correct = 0;
    let wrong = 0;
    let skip = 0;

    const rows = questions.map((q) => {
      const user = answers[q.id] || null;
      const ok = user === q.answer;
      if (!user) skip += 1;
      else if (ok) correct += 1;
      else wrong += 1;
      return { q, user, ok };
    });

    const pct = Math.round((correct / questions.length) * 100);

    quizView.classList.add("hidden");
    resultView.classList.remove("hidden");

    $("result-title").textContent = `${mod.short}: ${mod.title}`;
    $("score-pct").textContent = `${pct}%`;
    $("score-ring").style.setProperty("--pct", String(pct));
    $("score-summary").textContent = `Bạn đúng ${correct}/${questions.length} câu.`;
    $("stat-correct").textContent = String(correct);
    $("stat-wrong").textContent = String(wrong);
    $("stat-skip").textContent = String(skip);

    $("review-wrap").classList.remove("hidden");
    $("review-list").innerHTML = rows
      .map(({ q, user, ok }) => {
        const status = !user ? "wrong" : ok ? "correct" : "wrong";
        const badge = !user
          ? `<span class="badge bad">Chưa trả lời</span>`
          : ok
            ? `<span class="badge ok">Đúng</span>`
            : `<span class="badge bad">Sai</span>`;

        return `<article class="review-item ${status}">
          ${badge}
          <h3>Câu ${q.id}. ${escapeHtml(q.text)}</h3>
          <p class="choice-line">Bạn chọn: <strong>${user ? user + ". " + escapeHtml(q.options[user]) : "—"}</strong></p>
          <p class="choice-line">Đáp án đúng: <strong>${q.answer}. ${escapeHtml(q.options[q.answer])}</strong></p>
          <div class="knowledge">
            <b>Giải thích / kiến thức</b>
            ${escapeHtml((q.explain || "").trim())}
          </div>
        </article>`;
      })
      .join("");

    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function fillSlideBanner(mid) {
    const banner = $("slide-banner");
    if (!banner || !window.LEARN_PATH) return;
    const unit = window.LEARN_PATH.units.find((u) =>
      u.modules.some((m) => m.id === mid)
    );
    if (!unit?.slides) return;
    banner.classList.remove("hidden");
    banner.innerHTML = `
      <p><strong>Bước 1:</strong> Xem slides lý thuyết trước — ${escapeHtml(unit.slides.label)}</p>
      <a class="btn btn-primary" href="${unit.slides.url}" target="_blank" rel="noopener">Mở slides</a>
    `;
  }
})();
