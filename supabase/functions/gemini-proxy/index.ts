// Supabase Edge Function: gemini-proxy
// 목적: Gemini API 키를 서버에서만 사용(브라우저 노출 금지) + 스캔 한도 서버측 강제.
// 클라이언트는 { model, body } 만 보내고 결과(JSON)만 받습니다.
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

const FREE_SCAN_LIMIT = 10;      // 무료 플랜 총 누적 (index.html 과 동일)
const STUDENT_DAILY_LIMIT = 20;  // 결제중 학원 학생 일일

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
// 한국시간(KST) 기준 오늘 (일일 한도 리셋 기준)
function kstToday() {
  return new Date(Date.now() + 9 * 3600 * 1000).toISOString().slice(0, 10);
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

    const { model, body } = await req.json();

    // 2) 이미지 스캔이면 서버측 한도 검증 + 카운트 (텍스트 호출은 통과)
    const isScan = JSON.stringify(body ?? {}).includes("inline_data");
    if (isScan) {
      const { data: m } = await svc.from("members")
        .select("plan, scan_count, daily_scan_count, daily_scan_date, org_id, org_role, org_status")
        .eq("id", user.id).single();
      if (m) {
        let unlimited = (m.plan === "premium");
        let studentDaily = false;
        if (!unlimited && m.org_id &&
            (m.org_role === "owner" || (m.org_role === "student" && m.org_status === "approved"))) {
          const { data: org } = await svc.from("orgs").select("billing_active").eq("id", m.org_id).single();
          if (org?.billing_active) { m.org_role === "owner" ? (unlimited = true) : (studentDaily = true); }
        }
        if (!unlimited) {
          const today = kstToday();
          if (studentDaily) {
            const used = (m.daily_scan_date === today) ? (m.daily_scan_count || 0) : 0;
            if (used >= STUDENT_DAILY_LIMIT) {
              return json({ error: { code: "scan_limit", scope: "daily", message: "오늘 스캔 한도에 도달했어요" } });
            }
            await svc.from("members").update({
              daily_scan_count: used + 1, daily_scan_date: today, scan_count: (m.scan_count || 0) + 1,
            }).eq("id", user.id);
          } else {
            if ((m.scan_count || 0) >= FREE_SCAN_LIMIT) {
              return json({ error: { code: "scan_limit", scope: "free", message: "무료 스캔을 모두 사용했어요" } });
            }
            await svc.from("members").update({ scan_count: (m.scan_count || 0) + 1 }).eq("id", user.id);
          }
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
