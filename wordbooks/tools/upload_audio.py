#!/usr/bin/env python3
"""
로컬 audio/(w, s)의 mp3를 Supabase Storage 'audio' 공개 버킷에 업로드.
- 버킷 없으면 생성(public). upsert로 재실행 안전.
- 앱은 https://<proj>.supabase.co/storage/v1/object/public/audio/w|s/<word>.mp3 재생.

실행:
  export SB_URL="https://ziatqkjlafucqtwshhla.supabase.co"
  export SB_SERVICE_KEY="<service_role 키>"     # ⚠️ 비공개
  python3 tools/upload_audio.py                  # 미리보기(개수)
  python3 tools/upload_audio.py --go             # 업로드
"""
import os, sys, json, time, socket, urllib.request, urllib.error
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent   # voca/
AUD = REPO / "audio"
SB_URL = os.environ.get("SB_URL", "").rstrip("/")
KEY = os.environ.get("SB_SERVICE_KEY", "")
BUCKET = "audio"
GO = "--go" in sys.argv

def _req(method, path, data=None, ctype=None, extra=None, tries=5):
    last = None
    for attempt in range(tries):
        r = urllib.request.Request(SB_URL + path, data=data, method=method)
        r.add_header("apikey", KEY); r.add_header("Authorization", "Bearer " + KEY)
        if ctype: r.add_header("Content-Type", ctype)
        for k, v in (extra or {}).items(): r.add_header(k, v)
        try:
            with urllib.request.urlopen(r, timeout=120) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as e:
            body = e.read()
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                last = e; time.sleep(1.5 * (attempt + 1)); continue   # 일시적 서버오류 재시도
            return e.code, body
        except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError, OSError) as e:
            last = e
            if attempt < tries - 1:
                time.sleep(1.5 * (attempt + 1)); continue              # 네트워크 타임아웃 재시도
    return 0, (f"network error after {tries} tries: {last}".encode())

def ensure_bucket():
    st, body = _req("POST", "/storage/v1/bucket",
                    data=json.dumps({"id": BUCKET, "name": BUCKET, "public": True}).encode(),
                    ctype="application/json")
    if st in (200, 201): print(f"버킷 '{BUCKET}' 생성(public)")
    elif st in (400, 409): print(f"버킷 '{BUCKET}' 이미 있음")
    else: print(f"버킷 생성 응답 {st}: {body[:160]}")

def main():
    files = sorted(AUD.glob("*/*.mp3")) if AUD.exists() else []
    print(f"[plan] 로컬 mp3 {len(files)}개 · 대상 버킷='{BUCKET}'")
    print(f"  SB_URL={'OK' if SB_URL else 'MISSING'}  KEY={'OK' if KEY else 'MISSING'}")
    if not GO:
        print("\n(dry-run) 실제 업로드는 --go"); return
    if not (SB_URL and KEY) or "여기에" in KEY or any(ord(c) > 127 for c in KEY):
        print("ERROR: SB_URL / SB_SERVICE_KEY 환경변수에 실제 값 필요"); sys.exit(1)
    ensure_bucket()
    ok = fail = 0
    for f in files:
        rel = f"{f.parent.name}/{f.name}"          # w/enhance.mp3
        st, body = _req("POST", f"/storage/v1/object/{BUCKET}/{rel}",
                        data=f.read_bytes(), ctype="audio/mpeg",
                        extra={"x-upsert": "true", "cache-control": "31536000"})
        if st in (200, 201): ok += 1
        else:
            fail += 1; print(f"  FAIL {rel}: {st} {body[:120]}")
            if b"Invalid Compact JWS" in body or b"Unauthorized" in body or st == 401:
                print("\n⛔ SB_SERVICE_KEY 가 유효한 service_role 키가 아니에요.")
                print("   Supabase → Settings → API → 'service_role' secret (eyJ... 로 시작) 복사해서 다시 export 하세요.")
                break
        if (ok + fail) % 50 == 0: print(f"  {ok+fail}/{len(files)} (ok={ok})")
    print(f"\n완료. 업로드 {ok} · 실패 {fail}.")
    if ok: print(f"  예: {SB_URL}/storage/v1/object/public/{BUCKET}/{files[0].parent.name}/{files[0].name}")

if __name__ == "__main__":
    main()
