(() => {
  const STUDENT_KEY = "thvp-student";
  const cfg = () => window.SUPABASE_CONFIG || {};

  function configured() {
    return Boolean(cfg().url && cfg().anonKey);
  }

  function getClient() {
    if (!configured()) return null;
    if (!window.supabase?.createClient) {
      console.warn("Supabase SDK chưa tải.");
      return null;
    }
    if (!window.__thvpSb) {
      window.__thvpSb = window.supabase.createClient(cfg().url, cfg().anonKey);
    }
    return window.__thvpSb;
  }

  async function rpc(name, args) {
    const sb = getClient();
    if (!sb) throw new Error("Chưa cấu hình Supabase (supabase-config.js).");
    const { data, error } = await sb.rpc(name, args);
    if (error) throw error;
    return data;
  }

  function getStudent() {
    try {
      const raw = localStorage.getItem(STUDENT_KEY);
      if (!raw) return null;
      const s = JSON.parse(raw);
      if (!s?.id || !s?.code) return null;
      return s;
    } catch {
      return null;
    }
  }

  function setStudent(s) {
    localStorage.setItem(STUDENT_KEY, JSON.stringify(s));
  }

  function clearStudent() {
    localStorage.removeItem(STUDENT_KEY);
  }

  async function login(code, name) {
    const row = await rpc("login_student", {
      p_code: String(code || "").trim(),
      p_name: String(name || "").trim(),
    });
    const student = {
      id: row.id,
      code: row.code,
      name: row.name,
    };
    setStudent(student);
    return student;
  }

  function logout() {
    clearStudent();
  }

  async function heartbeat() {
    const s = getStudent();
    if (!s) return;
    try {
      await rpc("student_heartbeat", { p_student_id: s.id });
    } catch (e) {
      console.warn("heartbeat", e);
    }
  }

  function scopeFromStorageKey(storageKey) {
    if (storageKey === "thvp-quiz-mixed") return "mixed";
    const m = /^thvp-quiz-m(\d+)$/.exec(storageKey || "");
    return m ? `m${m[1]}` : storageKey || "unknown";
  }

  async function syncProgress({ storageKey, answers, index, sessionIds, redoWrongMode, questions }) {
    const s = getStudent();
    if (!s || !configured()) return;

    let correct = 0;
    let wrong = 0;
    const answered = Object.keys(answers || {});
    for (const q of questions || []) {
      const a = answers[q.id];
      if (!a) continue;
      if (a === q.answer) correct += 1;
      else wrong += 1;
    }
    const total = (questions || []).length || 1;
    const percent = Math.round((correct / total) * 100);
    const payload = {
      answers,
      index,
      ids: sessionIds || null,
      redoWrongMode: Boolean(redoWrongMode),
      redoWrongIds: redoWrongMode ? (questions || []).map((q) => q.id) : null,
      ts: Date.now(),
    };

    await rpc("upsert_quiz_progress", {
      p_student_id: s.id,
      p_scope: scopeFromStorageKey(storageKey),
      p_answered_count: answered.length,
      p_correct_count: correct,
      p_wrong_count: wrong,
      p_percent: percent,
      p_question_index: index || 0,
      p_payload: payload,
    });
  }

  async function fetchProgress(storageKey) {
    const s = getStudent();
    if (!s || !configured()) return null;
    return rpc("get_quiz_progress", {
      p_student_id: s.id,
      p_scope: scopeFromStorageKey(storageKey),
    });
  }

  async function saveAttempt({
    storageKey,
    reviewRows,
    correct,
    wrong,
    skip,
    percent,
    mode,
    startedAt,
  }) {
    const s = getStudent();
    if (!s || !configured()) return null;

    const answers = (reviewRows || []).map((r) => ({
      question_id: String(r.q?.poolId || r.q?.id || ""),
      selected: r.user,
      correct_answer: r.q?.answer,
      is_correct: Boolean(r.ok),
      answered_at: new Date().toISOString(),
    }));

    return rpc("save_quiz_attempt", {
      p_student_id: s.id,
      p_scope: scopeFromStorageKey(storageKey),
      p_correct: correct,
      p_wrong: wrong,
      p_skip: skip,
      p_percent: percent,
      p_mode: mode || "full",
      p_started_at: startedAt ? new Date(startedAt).toISOString() : new Date().toISOString(),
      p_answers: answers,
    });
  }

  async function adminFetch(adminKey, body = {}) {
    const action = body.action || "overview";
    const attemptId = body.attempt_id || null;

    // RPC trước (chạy APPLY_ADMIN_NOW.sql). Edge Function chỉ là dự phòng.
    if (configured()) {
      try {
        return await rpc("admin_dashboard", {
          p_admin_key: adminKey,
          p_action: action,
          p_attempt_id: attemptId,
        });
      } catch (e) {
        const msg = String(e?.message || e);
        const missingFn = /could not find|does not exist|PGRST202/i.test(msg);
        if (!missingFn) throw e;
        if (!cfg().adminFunctionUrl) {
          throw new Error(
            "Chưa có hàm admin_dashboard. Chạy file supabase/APPLY_ADMIN_NOW.sql trong SQL Editor."
          );
        }
      }
    }

    const url = cfg().adminFunctionUrl;
    if (!url) throw new Error("Chưa cấu hình adminFunctionUrl trong supabase-config.js");
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        apikey: cfg().anonKey,
        Authorization: `Bearer ${cfg().anonKey}`,
        "x-admin-key": adminKey,
      },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
  }

  let syncTimer = null;
  function syncProgressDebounced(args) {
    clearTimeout(syncTimer);
    syncTimer = setTimeout(() => {
      syncProgress(args).catch((e) => console.warn("syncProgress", e));
    }, 600);
  }

  function startHeartbeat(intervalMs = 30000) {
    heartbeat();
    const id = setInterval(heartbeat, intervalMs);
    window.addEventListener("focus", heartbeat);
    return () => {
      clearInterval(id);
      window.removeEventListener("focus", heartbeat);
    };
  }

  window.THVP_API = {
    configured,
    getClient,
    getStudent,
    login,
    logout,
    heartbeat,
    syncProgress,
    syncProgressDebounced,
    fetchProgress,
    saveAttempt,
    adminFetch,
    startHeartbeat,
    scopeFromStorageKey,
    STUDENT_KEY,
  };
})();
