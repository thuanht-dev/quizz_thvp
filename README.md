# THVP Quiz

Cổng học + quiz trắc nghiệm (static) trên Vercel.

## Chạy local

Mở `index.html`, hoặc từ thư mục cha mở `BAT_DAU_HOC.html`.

## Cấu trúc

```
index.html      Cổng học (entry)
quiz.html       Player quiz
admin.html      Dashboard giáo viên
css/            styles, home, quiz, admin
js/             config, api, auth, app, learn-path, whats-new
data/           quiz-data.js
supabase/       schema.sql + Edge Function (dự phòng)
docs/           hướng dẫn chi tiết
```

## Backend

Xem [docs/HUONG_DAN_BACKEND.md](docs/HUONG_DAN_BACKEND.md).

Cấu hình: `js/config.js` (URL + anon key).
