# Hướng dẫn backend Supabase + Vercel

Site quiz HTML tĩnh trên Vercel kết nối **Supabase** để: đăng nhập Mã+Tên, lưu tiến độ/điểm, lịch sử làm bài, dashboard giáo viên.

## 1. Tạo project Supabase

1. Vào [https://supabase.com](https://supabase.com) → New project
2. Ghi lại:
   - **Project URL** (Settings → API → Project URL)
   - **anon public** key (Settings → API → `anon` `public`)
   - Không đưa **service_role** key vào frontend

## 2. Chạy schema SQL

1. Supabase → SQL Editor → New query
2. Dán toàn bộ nội dung file `supabase/schema.sql`
3. Run

File tạo bảng `students`, `quiz_progress`, `quiz_attempts`, `quiz_attempt_answers`, bật RLS (chặn truy cập trực tiếp), và các RPC: `login_student`, `student_heartbeat`, `upsert_quiz_progress`, `get_quiz_progress`, `save_quiz_attempt`.

## 3. Deploy Edge Function admin

Cần [Supabase CLI](https://supabase.com/docs/guides/cli).

```bash
cd quiz
supabase login
supabase link --project-ref YOUR_PROJECT_REF

# Secret mã admin (tự đặt, không commit)
supabase secrets set ADMIN_KEY=ma-bi-mat-cua-ban

# Deploy (thư mục functions đã có sẵn)
supabase functions deploy admin-dashboard
```

URL function dạng:

`https://YOUR_PROJECT_REF.supabase.co/functions/v1/admin-dashboard`

Nếu CLI chưa khởi tạo local, copy thư mục `supabase/functions/admin-dashboard` vào project Supabase local rồi deploy.

## 4. Điền `supabase-config.js`

Mở `quiz/supabase-config.js`:

```js
window.SUPABASE_CONFIG = {
  url: "https://xxxx.supabase.co",
  anonKey: "eyJhbGciOi...",
  adminFunctionUrl: "https://xxxx.supabase.co/functions/v1/admin-dashboard",
};
```

Anon key được phép public trên frontend. **Không** commit `ADMIN_KEY`.

## 5. Deploy lại Vercel

Repo deploy là thư mục `quiz` (hoặc root chứa các file HTML này):

```bash
cd quiz
git add -A
git commit -m "Add Supabase auth, progress sync, and teacher dashboard"
git push
```

Vercel sẽ redeploy tự động nếu đã nối GitHub. Kiểm tra:

- Học viên: `home.html` → Đăng nhập (Mã + Tên) → làm quiz
- Giáo viên: `admin.html` → nhập `ADMIN_KEY` → xem online / điểm / lịch sử

Site hiện tại: https://quizz-mos.vercel.app

## Luồng dữ liệu (tóm tắt)

| Thành phần | Vai trò |
|---|---|
| `auth.js` | Form Mã+Tên, chặn quiz nếu đã cấu hình backend, logout |
| `api.js` | RPC + heartbeat 30s + sync progress/attempt |
| `app.js` | Debounce upsert tiến độ; lưu attempt khi xem kết quả; merge cloud nếu mới hơn local |
| `admin.html` | Gọi Edge Function với header `x-admin-key` |
| Edge Function | Dùng service_role đọc toàn bộ lớp |

**Online** = `last_seen_at` trong 2 phút gần nhất (heartbeat mỗi 30s + lúc login/focus).

## Bảo mật (môi trường lớp)

- Học viên không có mật khẩu → người biết mã có thể giả danh. Chấp nhận cho lớp học.
- Dashboard GV khóa bằng `ADMIN_KEY` qua Edge Function (không để service_role trên browser).

## Kiểm tra nhanh sau setup

1. Đăng nhập hai trình duyệt với hai mã khác nhau → thấy 2 dòng ở admin.
2. Làm vài câu quiz → bảng điểm theo scope (`m1`…`m6`, `mixed`) cập nhật.
3. Bấm tổng kết → có dòng trong “Lịch sử làm bài” → Chi tiết đúng/sai từng câu.
4. Để yên > 2 phút không tương tác → học viên chuyển khỏi “Đang online”.

## File liên quan

- `supabase/schema.sql`
- `supabase/functions/admin-dashboard/index.ts`
- `supabase-config.js`
- `api.js` · `auth.js` · `app.js` · `admin.html`
