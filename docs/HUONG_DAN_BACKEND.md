# Hướng dẫn backend Supabase + Vercel

Site quiz HTML tĩnh trên Vercel kết nối **Supabase** để: đăng nhập Mã+Tên, lưu tiến độ/điểm, lịch sử làm bài, dashboard giáo viên.

## 1. Tạo project Supabase

1. Vào [https://supabase.com](https://supabase.com) → New project
2. Ghi lại:
   - **Project URL** (Settings → API → Project URL)
   - **anon public** key (Settings → API)
   - Không đưa **service_role** key vào frontend

## 2. Chạy schema SQL

1. Supabase → SQL Editor → New query
2. Dán toàn bộ [`supabase/schema.sql`](../supabase/schema.sql) (gồm bảng, RPC học viên, và `admin_dashboard`)
3. Run

Mã GV mặc định trong RPC: `teddy2608` (đổi trong SQL nếu cần).

## 3. Điền `js/config.js`

```js
window.SUPABASE_CONFIG = {
  url: "https://xxxx.supabase.co",
  anonKey: "eyJhbGciOi... hoặc sb_publishable_...",
  // Tùy chọn — Edge Function dự phòng:
  adminFunctionUrl: "https://xxxx.supabase.co/functions/v1/admin-dashboard",
};
```

Anon key được phép public trên frontend. **Không** commit service_role.

## 4. Edge Function (tùy chọn)

Dashboard ưu tiên gọi RPC `admin_dashboard`. Edge Function chỉ là dự phòng:

```bash
cd quiz
supabase link --project-ref YOUR_REF
supabase secrets set ADMIN_KEY=teddy2608
supabase functions deploy admin-dashboard
```

## 5. Deploy Vercel

Repo deploy = thư mục `quiz` (GitHub `quizz_thvp`):

```bash
git add -A
git commit -m "Restructure quiz app layout"
git push
```

Kiểm tra:

- Học viên: `index.html` → Đăng nhập (Mã + Tên) → làm quiz
- Giáo viên: `admin.html` → nhập mã GV → xem online / điểm / lịch sử

Site: https://quizz-mos.vercel.app

## Luồng dữ liệu

| Thành phần | Vai trò |
|---|---|
| `js/auth.js` | Form Mã+Tên, gate quiz, logout |
| `js/api.js` | RPC + heartbeat + sync progress/attempt |
| `js/app.js` | Debounce progress; lưu attempt khi tổng kết |
| `admin.html` | Gọi `admin_dashboard` RPC (hoặc Edge Function) |

**Online** = `last_seen_at` trong 2 phút (heartbeat 30s).

## File liên quan

- `supabase/schema.sql`
- `supabase/functions/admin-dashboard/index.ts`
- `js/config.js` · `js/api.js` · `js/auth.js` · `js/app.js`
