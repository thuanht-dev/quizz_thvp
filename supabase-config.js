// Điền URL + anon key từ Supabase → Project Settings → API
// Anon key là public (dùng trên frontend). Không đưa service_role key vào đây.

window.SUPABASE_CONFIG = {
  url: "https://mbwyyhqydmbfgyfaueiv.supabase.co", // ví dụ: https://xxxx.supabase.co
  anonKey: "sb_publishable_ZSlxDCnllffgnvmyamymeQ_gnfl2uLz", // ví dụ: eyJhbGciOi...
  // URL Edge Function admin (sau khi deploy):
  // https://xxxx.supabase.co/functions/v1/admin-dashboard
  adminFunctionUrl: "",
};
