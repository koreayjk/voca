#!/usr/bin/env python3
"""
공식 단어장(Day1~30) 단어·예문 음원을 Google Cloud Text-to-Speech(정식 GA)로 1회 생성 → mp3.
- Gemini와 별개의 'Cloud Text-to-Speech API'. 할당량 넉넉, Neural2 음성, MP3 직접 반환.
- 단어: audio/w/<safe-en>.mp3 · 예문: audio/s/<safe-en>.mp3
- 멱등: 이미 있는 mp3는 건너뜀(--force 면 재생성). 생성 후 upload_audio.py 로 Storage 업로드.

선행(1회): Google Cloud Console에서 프로젝트에 **Cloud Text-to-Speech API 사용 설정(Enable)**.
  (API 키가 특정 API로 제한돼 있으면 TTS API도 허용해야 함)

실행:
  export GOOGLE_API_KEY="AIza...키"          # GEMINI_API_KEY 도 인식
  python3 tools/gen_audio.py                  # dry-run
  python3 tools/gen_audio.py --go             # 전체 생성
  python3 tools/gen_audio.py --go --limit 30  # 테스트
  옵션: GOOGLE_TTS_VOICE(기본 en-US-Neural2-F) · GOOGLE_TTS_LANG(en-US) · GOOGLE_TTS_RATE(0.95)
  음성 예: en-US-Neural2-C/D/F/J, en-US-Studio-O(최고급), en-GB-Neural2-B
"""
import os, sys, json, base64, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
AUD = REPO / "audio"
KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or ""
VOICE = os.environ.get("GOOGLE_TTS_VOICE", "en-US-Neural2-F")
LANG = os.environ.get("GOOGLE_TTS_LANG", "en-US")
RATE = float(os.environ.get("GOOGLE_TTS_RATE", "0.95"))
DELAY = float(os.environ.get("GOOGLE_TTS_DELAY", "0.15"))
GO = "--go" in sys.argv
FORCE = "--force" in sys.argv
LIMIT = None
for i, a in enumerate(sys.argv):
    if a == "--limit" and i+1 < len(sys.argv): LIMIT = int(sys.argv[i+1])
DAYS = list(range(1, 31))

def safe(en): return "".join(c for c in (en or "").lower() if c.isalnum())

def collect():
    import glob
    items, seen = [], set()
    files = sorted(f for f in glob.glob(str(ROOT/"suneung-*-day*.json")) if ".scaffold." not in f)
    for f in files:                       # 모든 책(기본+핵심+고난도+…) 단어 포함, 중복 제거
        for w in json.load(open(f))["words"]:
            sf = safe(w["en"])
            if sf in seen: continue
            seen.add(sf)
            items.append(("w", w["en"], AUD/"w"/f"{sf}.mp3"))
            ex = (w["meanings"][0].get("ex") or "").strip()
            if ex: items.append(("s", ex, AUD/"s"/f"{sf}.mp3"))
    return items

def tts(text):
    """Google Cloud TTS → mp3 bytes."""
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={KEY}"
    body = {"input": {"text": text},
            "voice": {"languageCode": LANG, "name": VOICE},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": RATE}}
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode()
    d = json.loads(raw)
    if "audioContent" not in d:
        raise RuntimeError("오디오 없음 → " + raw[:300])
    return base64.b64decode(d["audioContent"])

def save_mp3(data, outp):
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_bytes(data)

def main():
    items = collect()
    todo = [it for it in items if FORCE or not it[2].exists()]
    if LIMIT: todo = todo[:LIMIT]
    print(f"[plan] 대상 {len(items)}개 · 생성 필요 {len(todo)}개 · voice={VOICE} rate={RATE}")
    print(f"  GOOGLE_API_KEY={'OK' if KEY else 'MISSING'}  (Cloud Text-to-Speech API)")
    if not GO:
        print("\n(dry-run) 실제 생성은 --go. 선행: Cloud Text-to-Speech API Enable.")
        return
    if not KEY or "여기에" in KEY or any(ord(c) > 127 for c in KEY):
        print("ERROR: GOOGLE_API_KEY(또는 GEMINI_API_KEY) 환경변수에 실제 키 필요"); sys.exit(1)
    ok = fail = 0; consec = 0; i = 0
    while i < len(todo):
        kind, text, outp = todo[i]
        try:
            save_mp3(tts(text), outp); ok += 1; consec = 0; i += 1
            if ok % 50 == 0 or i == len(todo): print(f"  {ok} 생성 ({i}/{len(todo)})  최근:{outp.name}")
            time.sleep(DELAY)
        except urllib.error.HTTPError as e:
            err = e.read()[:200]
            if e.code in (429, 503):
                consec += 1
                if consec >= 6:
                    print(f"\n⛔ {e.code} 반복 — 할당량/일시오류. 잠시 후 재실행하면 이어서 됩니다."); break
                w = min(40, 5*consec); print(f"  ⏳ {e.code} — {w}s 대기 재시도 ({outp.name})"); time.sleep(w)
            else:
                fail += 1; i += 1
                print(f"  FAIL {outp.name}: HTTP {e.code} {err}")
                if e.code in (400, 403):
                    print("   ↳ 403/400이면: Cloud Text-to-Speech API 미사용설정 또는 키 제한일 수 있어요.");
                time.sleep(1)
        except Exception as e:
            fail += 1; i += 1; print(f"  FAIL {outp.name}: {e}"); time.sleep(1)
    print(f"\n완료. 생성 {ok} · 실패 {fail}.  다음: python3 tools/upload_audio.py --go")

if __name__ == "__main__":
    main()
