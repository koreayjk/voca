// Supabase Edge Function: gemini-proxy
// 목적: Gemini API 키를 서버에서만 사용(브라우저 노출 금지) + 스캔 한도 서버측 강제.
// 클라이언트는 { model, body, tz } 만 보내고 결과(JSON)만 받습니다.
// 이미지(inline_data 포함) 호출 = "스캔"으로 간주 → 로그인 사용자별 한도 검증·카운트를
//   service_role 로 서버에서 처리(클라이언트 우회 불가). 텍스트 호출(뜻/예문)은 카운트 안 함.
// Secrets: GEMINI_KEY, (자동주입) SUPABASE_URL, SB_SERVICE_ROLE_KEY
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const GEMINI_KEY = Deno.env.get("GEMINI_KEY") ?? "";
const svc = createClient(
  Deno.env.get("SUPABASE_URL") ?? "",
  Deno.env.get("SB_SERVICE_ROLE_KEY") ?? "",
);

// ── 스캔 한도 (index.html 의 같은 이름 상수와 반드시 같이 고칠 것) ──────────
// 무료는 '평생 몇 장'이 아니라 '하루 몇 장'이다. 일일 한도는 매일 돌아올 이유가
// 되지만 평생 한도는 다 쓰면 그걸로 끝이라 앱을 지울 이유가 된다.
// 장당 원가 약 $0.007. 그래서 '무제한'은 결제중 학원의 원장 하나뿐이다.
// 프리미엄도 상한이 있다 — $3.99 에서 Stripe 수수료를 빼면 실수령 $3.57,
// 손익분기가 월 510장이라 무제한이면 많이 쓰는 한 명이 구독료보다 더 쓴다.
// 하루·월을 둘 다 거는 이유: 하루만 두면 월 900장까지 가서 적자고,
//                            월만 두면 하루에 몰아 써서 남용 탐지가 어렵다.
const FREE_DAILY_LIMIT = 5,     FREE_MONTHLY_LIMIT = 60;      // 최악 원가 $0.42 (획득 비용)
const STUDENT_DAILY_LIMIT = 10, STUDENT_MONTHLY_LIMIT = 150;  // 최악 $1.05 / 실수령 $2.90
const PREMIUM_DAILY_LIMIT = 30, PREMIUM_MONTHLY_LIMIT = 300;  // 최악 $2.10 / 실수령 $3.57

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
function json(obj: unknown, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}
// 한국시간(KST) 기준 오늘 — 시간대를 알 수 없을 때의 마지막 수단.
function kstToday() {
  return new Date(Date.now() + 9 * 3600 * 1000).toISOString().slice(0, 10);
}
// ── 일일 한도의 '오늘' 은 사용자가 있는 나라의 달력 날짜여야 한다 ──────────
// 예전엔 여기가 KST 로 못박혀 있었다. 그러면 텍사스 학생은 현지 오전 9~10시에
// 일일 한도가 리셋된다 — 아침에 갑자기 한도가 풀리고, 밤에 쓰면 다음 날 몫을
// 당겨 쓴다. 앱의 나머지(_todayStr)는 이미 현지 날짜를 쓰고 있어서 서버와 앱이
// 서로 다른 '오늘' 을 보고 있었다.
//
// 날짜 문자열을 그대로 받으면 매 요청마다 아무 날짜나 보내 한도를 무한히 리셋할
// 수 있다. 그래서 '시간대 이름' 만 받아 서버가 직접 날짜를 계산한다. Intl 이
// 모르는 이름은 예외를 던지므로 실제 존재하는 시간대만 통과하고, 실제 시간대
// 사이의 날짜 차이는 최대 하루라 악용 여지가 좁다.
function dateInTz(tz: unknown): string | null {
  if (!tz || typeof tz !== "string" || tz.length > 64 || !/^[A-Za-z0-9_+\-\/]+$/.test(tz)) return null;
  try {
    // en-CA 로케일이 YYYY-MM-DD 형식을 준다
    return new Intl.DateTimeFormat("en-CA", {
      timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit",
    }).format(new Date());
  } catch { return null; }
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return json({ error: { message: "Method not allowed" } });
  if (!GEMINI_KEY) return json({ error: { message: "GEMINI_KEY secret이 설정되지 않았어요" } });

  try {
    // 1) 로그인 사용자 검증 (anon 키만으로는 호출 불가 → Gemini 비용 남용 차단)
    const token = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
    const { data: ures } = token ? await svc.auth.getUser(token) : { data: { user: null } };
    const user = ures?.user;
    if (!user) return json({ error: { code: "auth", message: "로그인이 필요해요" } }, 401);

    const { model, body, tz } = await req.json();

    // 2) 이미지 스캔이면 서버측 한도 검증 + 카운트 (텍스트 호출은 통과)
    const isScan = JSON.stringify(body ?? {}).includes("inline_data");
    if (isScan) {
      // 월 컬럼이 아직 없는 DB(= scan-monthly-limit.sql 미실행)에서도 스캔이 죽지 않게
      // 한 번 더 시도한다. 폴백일 때는 월 한도를 건너뛰고 일일 한도만 건다.
      const COLS_FULL = "plan, scan_count, daily_scan_count, daily_scan_date, monthly_scan_count, monthly_scan_month, org_id, org_role, org_status, signup_tz";
      const COLS_BASE = "plan, scan_count, daily_scan_count, daily_scan_date, org_id, org_role, org_status, signup_tz";
      let hasMonthly = true;
      let { data: m, error: mErr } = await svc.from("members").select(COLS_FULL).eq("id", user.id).single();
      if (mErr) {
        hasMonthly = false;
        ({ data: m } = await svc.from("members").select(COLS_BASE).eq("id", user.id).single());
      }
      if (m) {
        // 등급을 먼저 정하고, 한도 검사는 한 번만 한다.
        let unlimited = false;                                   // 결제중 학원의 원장만
        let dayCap = FREE_DAILY_LIMIT, monCap = FREE_MONTHLY_LIMIT;
        if (m.plan === "premium") { dayCap = PREMIUM_DAILY_LIMIT; monCap = PREMIUM_MONTHLY_LIMIT; }
        if (m.org_id && (m.org_role === "owner" || (m.org_role === "student" && m.org_status === "approved"))) {
          const { data: org } = await svc.from("orgs").select("billing_active").eq("id", m.org_id).single();
          if (org?.billing_active) {
            if (m.org_role === "owner") unlimited = true;
            else if (m.plan !== "premium") { dayCap = STUDENT_DAILY_LIMIT; monCap = STUDENT_MONTHLY_LIMIT; }
          }
        }
        if (!unlimited) {
          // 사용자 현지 날짜 → 없거나 이상하면 가입 시 기록해 둔 시간대 → 그것도 없으면 KST
          const today = dateInTz(tz) || dateInTz(m.signup_tz) || kstToday();
          const month = today.slice(0, 7);                       // 'YYYY-MM'
          const dUsed = (m.daily_scan_date === today) ? (m.daily_scan_count || 0) : 0;
          if (dUsed >= dayCap) {
            return json({ error: { code: "scan_limit", scope: "daily", limit: dayCap, message: "오늘 스캔 한도에 도달했어요" } });
          }
          const mUsed = (hasMonthly && m.monthly_scan_month === month) ? (m.monthly_scan_count || 0) : 0;
          if (hasMonthly && mUsed >= monCap) {
            return json({ error: { code: "scan_limit", scope: "monthly", limit: monCap, message: "이번 달 스캔 한도에 도달했어요" } });
          }
          const patch: Record<string, unknown> = {
            daily_scan_count: dUsed + 1, daily_scan_date: today,
            scan_count: (m.scan_count || 0) + 1,
          };
          if (hasMonthly) { patch.monthly_scan_count = mUsed + 1; patch.monthly_scan_month = month; }
          await svc.from("members").update(patch).eq("id", user.id);
        }
      }
    }

    // 3) Gemini 호출 (키는 서버에서만)
    const safeModel = String(model || "gemini-2.5-flash").replace(/[^a-zA-Z0-9.\-]/g, "");
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${safeModel}:generateContent?key=${GEMINI_KEY}`;
    const gres = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body ?? {}),
    });
    const data = await gres.json();
    return json(data);
  } catch (e) {
    return json({ error: { message: String((e as Error)?.message || e) } });
  }
});
