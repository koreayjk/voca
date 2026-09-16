// ============================================================
// APNs (애플 푸시) 전송 — iOS 앱용
//
// 웹 푸시(VAPID)와 달리 애플은 '프로바이더 토큰'이라는 JWT 를 요구한다.
//   · .p8 인증 키 파일 하나로 서명(ES256)한다 — 개발자 계정에서 한 번 만들면 계속 쓴다
//   · 토큰은 최대 1시간 유효. 매 요청마다 새로 만들면 애플이 TooManyProviderTokenUpdates
//     로 막으므로 30분 캐시한다.
//
// env: APNS_KEY_ID, APNS_TEAM_ID, APNS_PRIVATE_KEY(.p8 내용 전체), APNS_BUNDLE_ID
//      APNS_HOST(선택) — 'sandbox' 면 개발 빌드용 서버로 보낸다
//      (Xcode 에서 직접 설치한 빌드는 sandbox, TestFlight·앱스토어는 production)
// ============================================================

const PROD = 'https://api.push.apple.com';
const SANDBOX = 'https://api.sandbox.push.apple.com';

let _cached: { token: string; at: number } | null = null;

function b64url(src: ArrayBuffer | Uint8Array): string {
  const b = src instanceof Uint8Array ? src : new Uint8Array(src);
  let s = '';
  for (const c of b) s += String.fromCharCode(c);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

// Supabase 시크릿에 넣을 때 줄바꿈이 \n 문자열로 들어오는 경우가 흔해서 되돌려준다.
function pemToPkcs8(pem: string): Uint8Array {
  const body = pem
    .replace(/\\n/g, '\n')
    .replace(/-----BEGIN [^-]+-----/g, '')
    .replace(/-----END [^-]+-----/g, '')
    .replace(/\s+/g, '');
  const raw = atob(body);
  const out = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
  return out;
}

async function providerToken(keyId: string, teamId: string, p8: string): Promise<string> {
  const now = Math.floor(Date.now() / 1000);
  if (_cached && now - _cached.at < 1800) return _cached.token;

  const key = await crypto.subtle.importKey(
    'pkcs8', pemToPkcs8(p8), { name: 'ECDSA', namedCurve: 'P-256' }, false, ['sign'],
  );
  const enc = new TextEncoder();
  const head = b64url(enc.encode(JSON.stringify({ alg: 'ES256', kid: keyId })));
  const body = b64url(enc.encode(JSON.stringify({ iss: teamId, iat: now })));
  const sig = await crypto.subtle.sign({ name: 'ECDSA', hash: 'SHA-256' }, key, enc.encode(head + '.' + body));
  const token = `${head}.${body}.${b64url(sig)}`;
  _cached = { token, at: now };
  return token;
}

export type ApnsResult = { ok: boolean; status: number; reason: string; gone: boolean };

export function apnsConfigured(): boolean {
  return !!(Deno.env.get('APNS_KEY_ID') && Deno.env.get('APNS_TEAM_ID') && Deno.env.get('APNS_PRIVATE_KEY'));
}

export async function sendApns(
  deviceToken: string,
  payload: { title: string; body: string; badge: number; url: string },
): Promise<ApnsResult> {
  const keyId = Deno.env.get('APNS_KEY_ID') ?? '';
  const teamId = Deno.env.get('APNS_TEAM_ID') ?? '';
  const p8 = Deno.env.get('APNS_PRIVATE_KEY') ?? '';
  const topic = Deno.env.get('APNS_BUNDLE_ID') ?? 'app.imvoca';
  const preferred = (Deno.env.get('APNS_HOST') ?? '').toLowerCase() === 'sandbox' ? SANDBOX : PROD;

  const jwt = await providerToken(keyId, teamId, p8);
  const aps = {
    aps: {
      alert: { title: payload.title, body: payload.body },
      badge: payload.badge,
      sound: 'default',
      'thread-id': 'imvoca-review',
    },
    url: payload.url,
  };

  const post = (host: string) => fetch(`${host}/3/device/${deviceToken}`, {
    method: 'POST',
    headers: {
      authorization: `bearer ${jwt}`,
      'apns-topic': topic,
      'apns-push-type': 'alert',
      'apns-priority': '10',
      // 6시간 안에 못 받으면 버린다 (다음날 또 보내므로)
      'apns-expiration': String(Math.floor(Date.now() / 1000) + 6 * 3600),
      'apns-collapse-id': 'imvoca-review',
      'content-type': 'application/json',
    },
    body: JSON.stringify(aps),
  });

  let res = await post(preferred);
  let text = res.ok ? '' : await res.text();
  let reason = '';
  try { reason = text ? (JSON.parse(text).reason ?? text) : ''; } catch { reason = text; }

  // 같은 기기 토큰이라도 개발 빌드와 앱스토어 빌드는 서버가 다르다. 한쪽에서
  // BadDeviceToken 이 나면 반대쪽으로 한 번만 더 시도한다 (테스트 기기 때문에 흔하다).
  if (!res.ok && reason === 'BadDeviceToken') {
    const other = preferred === PROD ? SANDBOX : PROD;
    res = await post(other);
    text = res.ok ? '' : await res.text();
    try { reason = text ? (JSON.parse(text).reason ?? text) : ''; } catch { reason = text; }
  }

  // 앱 삭제·토큰 폐기 → 구독을 지워야 한다
  const gone = res.status === 410 || reason === 'Unregistered' || reason === 'BadDeviceToken';
  return { ok: res.ok, status: res.status, reason, gone };
}
