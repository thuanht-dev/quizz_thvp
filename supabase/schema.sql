-- THVP Quiz — schema + RLS + RPC (chạy 1 lần trong Supabase SQL Editor)

create extension if not exists "pgcrypto";

-- —— Tables ——
create table if not exists public.students (
  id uuid primary key default gen_random_uuid(),
  code text not null,
  name text not null,
  created_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  constraint students_code_unique unique (code)
);

create table if not exists public.quiz_progress (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students(id) on delete cascade,
  scope text not null,
  answered_count int not null default 0,
  correct_count int not null default 0,
  wrong_count int not null default 0,
  percent int not null default 0,
  question_index int not null default 0,
  payload jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  constraint quiz_progress_student_scope unique (student_id, scope)
);

create table if not exists public.quiz_attempts (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students(id) on delete cascade,
  scope text not null,
  started_at timestamptz not null default now(),
  finished_at timestamptz not null default now(),
  correct int not null default 0,
  wrong int not null default 0,
  skip int not null default 0,
  percent int not null default 0,
  mode text not null default 'full'
);

create table if not exists public.quiz_attempt_answers (
  id uuid primary key default gen_random_uuid(),
  attempt_id uuid not null references public.quiz_attempts(id) on delete cascade,
  question_id text not null,
  selected text,
  correct_answer text not null,
  is_correct boolean not null default false,
  answered_at timestamptz not null default now()
);

create index if not exists idx_students_last_seen on public.students (last_seen_at desc);
create index if not exists idx_progress_student on public.quiz_progress (student_id);
create index if not exists idx_attempts_student on public.quiz_attempts (student_id, finished_at desc);
create index if not exists idx_attempt_answers_attempt on public.quiz_attempt_answers (attempt_id);

-- —— RLS: khóa truy cập trực tiếp; chỉ dùng qua RPC / service_role ——
alter table public.students enable row level security;
alter table public.quiz_progress enable row level security;
alter table public.quiz_attempts enable row level security;
alter table public.quiz_attempt_answers enable row level security;

drop policy if exists students_no_direct on public.students;
create policy students_no_direct on public.students for all using (false) with check (false);

drop policy if exists progress_no_direct on public.quiz_progress;
create policy progress_no_direct on public.quiz_progress for all using (false) with check (false);

drop policy if exists attempts_no_direct on public.quiz_attempts;
create policy attempts_no_direct on public.quiz_attempts for all using (false) with check (false);

drop policy if exists answers_no_direct on public.quiz_attempt_answers;
create policy answers_no_direct on public.quiz_attempt_answers for all using (false) with check (false);

-- —— RPCs (SECURITY DEFINER) ——

create or replace function public.login_student(p_code text, p_name text)
returns public.students
language plpgsql
security definer
set search_path = public
as $$
declare
  v_code text := upper(trim(p_code));
  v_name text := trim(p_name);
  v_row public.students;
begin
  if v_code is null or v_code = '' or v_name is null or v_name = '' then
    raise exception 'Mã và tên không được trống';
  end if;
  if char_length(v_code) > 32 or char_length(v_name) > 80 then
    raise exception 'Mã hoặc tên quá dài';
  end if;

  insert into public.students (code, name, last_seen_at)
  values (v_code, v_name, now())
  on conflict (code) do update
    set name = excluded.name,
        last_seen_at = now()
  returning * into v_row;

  return v_row;
end;
$$;

create or replace function public.student_heartbeat(p_student_id uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.students
  set last_seen_at = now()
  where id = p_student_id;
end;
$$;

create or replace function public.upsert_quiz_progress(
  p_student_id uuid,
  p_scope text,
  p_answered_count int,
  p_correct_count int,
  p_wrong_count int,
  p_percent int,
  p_question_index int,
  p_payload jsonb
)
returns public.quiz_progress
language plpgsql
security definer
set search_path = public
as $$
declare
  v_row public.quiz_progress;
begin
  if not exists (select 1 from public.students where id = p_student_id) then
    raise exception 'Student không tồn tại';
  end if;

  insert into public.quiz_progress as qp (
    student_id, scope, answered_count, correct_count, wrong_count,
    percent, question_index, payload, updated_at
  ) values (
    p_student_id, p_scope, p_answered_count, p_correct_count, p_wrong_count,
    p_percent, p_question_index, coalesce(p_payload, '{}'::jsonb), now()
  )
  on conflict (student_id, scope) do update set
    answered_count = excluded.answered_count,
    correct_count = excluded.correct_count,
    wrong_count = excluded.wrong_count,
    percent = excluded.percent,
    question_index = excluded.question_index,
    payload = excluded.payload,
    updated_at = now()
  returning * into v_row;

  update public.students set last_seen_at = now() where id = p_student_id;
  return v_row;
end;
$$;

create or replace function public.get_quiz_progress(p_student_id uuid, p_scope text)
returns public.quiz_progress
language plpgsql
security definer
set search_path = public
as $$
declare
  v_row public.quiz_progress;
begin
  select * into v_row
  from public.quiz_progress
  where student_id = p_student_id and scope = p_scope;
  return v_row;
end;
$$;

create or replace function public.save_quiz_attempt(
  p_student_id uuid,
  p_scope text,
  p_correct int,
  p_wrong int,
  p_skip int,
  p_percent int,
  p_mode text,
  p_started_at timestamptz,
  p_answers jsonb
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_attempt_id uuid;
  v_item jsonb;
begin
  if not exists (select 1 from public.students where id = p_student_id) then
    raise exception 'Student không tồn tại';
  end if;

  insert into public.quiz_attempts (
    student_id, scope, started_at, finished_at,
    correct, wrong, skip, percent, mode
  ) values (
    p_student_id, p_scope, coalesce(p_started_at, now()), now(),
    p_correct, p_wrong, p_skip, p_percent, coalesce(p_mode, 'full')
  )
  returning id into v_attempt_id;

  if p_answers is not null then
    for v_item in select * from jsonb_array_elements(p_answers)
    loop
      insert into public.quiz_attempt_answers (
        attempt_id, question_id, selected, correct_answer, is_correct, answered_at
      ) values (
        v_attempt_id,
        coalesce(v_item->>'question_id', ''),
        v_item->>'selected',
        coalesce(v_item->>'correct_answer', ''),
        coalesce((v_item->>'is_correct')::boolean, false),
        coalesce((v_item->>'answered_at')::timestamptz, now())
      );
    end loop;
  end if;

  update public.students set last_seen_at = now() where id = p_student_id;
  return v_attempt_id;
end;
$$;

grant execute on function public.login_student(text, text) to anon, authenticated;
grant execute on function public.student_heartbeat(uuid) to anon, authenticated;
grant execute on function public.upsert_quiz_progress(uuid, text, int, int, int, int, int, jsonb) to anon, authenticated;
grant execute on function public.get_quiz_progress(uuid, text) to anon, authenticated;
grant execute on function public.save_quiz_attempt(uuid, text, int, int, int, int, text, timestamptz, jsonb) to anon, authenticated;

-- —— Admin dashboard RPC (mã GV; Edge Function là dự phòng) ——
-- Khóa dashboard = teddy2608

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

