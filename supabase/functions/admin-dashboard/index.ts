// Supabase Edge Function: admin-dashboard
// Deploy: supabase functions deploy admin-dashboard
// Secret: supabase secrets set ADMIN_KEY=your-secret

import { createClient } from "https://esm.sh/@supabase/supabase-js@2.49.1";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-admin-key",
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const adminKey = Deno.env.get("ADMIN_KEY") || "";
    const provided = req.headers.get("x-admin-key") || "";
    if (!adminKey || provided !== adminKey) {
      return json({ error: "Unauthorized" }, 401);
    }

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    const body = req.method === "POST" ? await req.json().catch(() => ({})) : {};
    const action = body.action || "overview";

    if (action === "attempt_detail") {
      const attemptId = body.attempt_id;
      if (!attemptId) return json({ error: "missing attempt_id" }, 400);
      const { data, error } = await supabase
        .from("quiz_attempt_answers")
        .select("question_id, selected, correct_answer, is_correct, answered_at")
        .eq("attempt_id", attemptId)
        .order("answered_at", { ascending: true });
      if (error) throw error;
      return json({ answers: data || [] });
    }

    const now = Date.now();
    const onlineMs = 2 * 60 * 1000;

    const { data: students, error: sErr } = await supabase
      .from("students")
      .select("id, code, name, created_at, last_seen_at")
      .order("last_seen_at", { ascending: false });
    if (sErr) throw sErr;

    const { data: progress, error: pErr } = await supabase
      .from("quiz_progress")
      .select("student_id, scope, answered_count, correct_count, wrong_count, percent, updated_at");
    if (pErr) throw pErr;

    const { data: attempts, error: aErr } = await supabase
      .from("quiz_attempts")
      .select("id, student_id, scope, finished_at, correct, wrong, skip, percent, mode")
      .order("finished_at", { ascending: false })
      .limit(300);
    if (aErr) throw aErr;

    const progressByStudent = {};
    for (const row of progress || []) {
      (progressByStudent[row.student_id] ||= {})[row.scope] = row;
    }

    const latestAttemptByStudent = {};
    for (const row of attempts || []) {
      if (!latestAttemptByStudent[row.student_id]) {
        latestAttemptByStudent[row.student_id] = row;
      }
    }

    const list = (students || []).map((s) => {
      const last = new Date(s.last_seen_at).getTime();
      const online = now - last <= onlineMs;
      return {
        ...s,
        online,
        progress: progressByStudent[s.id] || {},
        latest_attempt: latestAttemptByStudent[s.id] || null,
      };
    });

    const online = list.filter((s) => s.online);
    const recent = list.filter((s) => !s.online).slice(0, 20);

    return json({
      generated_at: new Date().toISOString(),
      online_count: online.length,
      student_count: list.length,
      online,
      recent,
      students: list,
      recent_attempts: (attempts || []).slice(0, 40),
    });
  } catch (err) {
    return json({ error: String(err?.message || err) }, 500);
  }
});

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}
