-- Chạy 1 lần trong Supabase → SQL Editor → Run
-- Khóa dashboard GV = teddy2608 (không dùng Edge Function)

create or replace function public.admin_dashboard(
  p_admin_key text,
  p_action text default 'overview',
  p_attempt_id uuid default null
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_online_ms interval := interval '2 minutes';
  v_now timestamptz := now();
  v_students jsonb;
  v_progress jsonb;
  v_attempts jsonb;
  v_answers jsonb;
  v_list jsonb;
  v_online jsonb;
  v_recent jsonb;
begin
  if p_admin_key is distinct from 'teddy2608' then
    raise exception 'Unauthorized';
  end if;

  if coalesce(p_action, 'overview') = 'attempt_detail' then
    if p_attempt_id is null then
      raise exception 'missing attempt_id';
    end if;
    select coalesce(jsonb_agg(to_jsonb(a) order by a.answered_at), '[]'::jsonb)
      into v_answers
    from public.quiz_attempt_answers a
    where a.attempt_id = p_attempt_id;
    return jsonb_build_object('answers', v_answers);
  end if;

  select coalesce(jsonb_agg(to_jsonb(s) order by s.last_seen_at desc), '[]'::jsonb)
    into v_students
  from public.students s;

  select coalesce(jsonb_agg(to_jsonb(p)), '[]'::jsonb)
    into v_progress
  from public.quiz_progress p;

  select coalesce(jsonb_agg(to_jsonb(t) order by t.finished_at desc), '[]'::jsonb)
    into v_attempts
  from (
    select id, student_id, scope, finished_at, correct, wrong, skip, percent, mode
    from public.quiz_attempts
    order by finished_at desc
    limit 300
  ) t;

  select coalesce(jsonb_agg(row_data), '[]'::jsonb)
    into v_list
  from (
    select jsonb_build_object(
      'id', s.id,
      'code', s.code,
      'name', s.name,
      'created_at', s.created_at,
      'last_seen_at', s.last_seen_at,
      'online', (s.last_seen_at >= v_now - v_online_ms),
      'progress', coalesce((
        select jsonb_object_agg(p.scope, jsonb_build_object(
          'student_id', p.student_id,
          'scope', p.scope,
          'answered_count', p.answered_count,
          'correct_count', p.correct_count,
          'wrong_count', p.wrong_count,
          'percent', p.percent,
          'updated_at', p.updated_at
        ))
        from public.quiz_progress p
        where p.student_id = s.id
      ), '{}'::jsonb),
      'latest_attempt', (
        select to_jsonb(a)
        from (
          select id, student_id, scope, finished_at, correct, wrong, skip, percent, mode
          from public.quiz_attempts
          where student_id = s.id
          order by finished_at desc
          limit 1
        ) a
      )
    ) as row_data
    from public.students s
    order by s.last_seen_at desc
  ) q;

  select coalesce(jsonb_agg(x), '[]'::jsonb)
    into v_online
  from jsonb_array_elements(v_list) x
  where (x->>'online')::boolean is true;

  select coalesce(jsonb_agg(x), '[]'::jsonb)
    into v_recent
  from (
    select x
    from jsonb_array_elements(v_list) x
    where (x->>'online')::boolean is not true
    limit 20
  ) q;

  return jsonb_build_object(
    'generated_at', v_now,
    'online_count', jsonb_array_length(v_online),
    'student_count', jsonb_array_length(v_list),
    'online', v_online,
    'recent', coalesce(v_recent, '[]'::jsonb),
    'students', v_list,
    'recent_attempts', coalesce(
      (select jsonb_agg(x) from (
        select x from jsonb_array_elements(v_attempts) x limit 40
      ) t),
      '[]'::jsonb
    )
  );
end;
$$;

grant execute on function public.admin_dashboard(text, text, uuid) to anon, authenticated;
