#!/usr/bin/env python3
"""
공식 단어장(Day1~30) 단어·예문 음원을 Gemini TTS로 1회 생성 → mp3 저장.
- 단어: audio/w/<safe-en>.mp3 · 예문: audio/s/<safe-en>.mp3 (repo 루트의 audio/)
- 앱은 저장된 mp3를 재생(있으면), 없으면 기존 기기 TTS로 폴백 → 재생 시 API 호출 0.
- 멱등: 이미 있는 mp3는 건너뜀(--force 면 재생성).

실행:
  export GEMINI_API_KEY="<Gemini API 키>"        # ⚠️ 비공개. 커밋/공유 금지
  python3 tools/gen_audio.py                      # dry-run(개수·예상만)
  python3 tools/gen_audio.py --go                 # 실제 생성
  python3 tools/gen_audio.py --go --limit 10      # 앞 10단어만(테스트)
  python3 tools/gen_audio.py --go --force         # 전체 재생성
  옵션: export GEMINI_TTS_VOICE="Kore" (기본) · GEMINI_TTS_MODEL="gemini-2.5-flash-preview-tts"
선행 없음. 생성 후 audio/ 가 repo에 포함되어 imvoca.app/audio/... 로 서빙됨.
"""
import os, sys, json, base64, time, subprocess, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # wordbooks/
REPO = ROOT.parent                                       # voca/ (repo root)
AUD = REPO / "audio"
KEY = os.environ.get("GEMINI_API_KEY", "")
VOICE = os.environ.get("GEMINI_TTS_VOICE", "Kore")
MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
GO = "--go" in sys.argv
FORCE = "--force" in sys.argv
LIMIT = None
for i,a in enumerate(sys.argv):
    if a == "--limit" and i+1 < len(sys.argv): LIMIT = int(sys.argv[i+1])
DAYS = list(range(1, 31))

def safe(en):
    return "".join(c for c in (en or "").lower() if c.isalnum())

def collect():
    items = []  # (kind, text, outpath)
    seen = set()
    for n in DAYS:
        for w in json.load(open(ROOT/f"suneung-basic-day{n}.json"))["words"]:
            en = w["en"]; sf = safe(en)
            if sf in seen: continue
            seen.add(sf)
            items.append(("w", en, AUD/"w"/f"{sf}.mp3"))
            ex = (w["meanings"][0].get("ex") or "").strip()
            if ex: items.append(("s", ex, AUD/"s"/f"{sf}.mp3"))
    return items

def tts(text):
    """Gemini TTS → PCM(s16le,24k,mono) bytes."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}"
    body = {"contents":[{"parts":[{"text":text}]}],
            "generationConfig":{"responseModalities":["AUDIO"],
              "speechConfig":{"voiceConfig":{"prebuiltVoiceConfig":{"voiceName":VOICE}}}}}
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode())
    part = d["candidates"][0]["content"]["parts"][0]
    return base64.b64decode(part["inlineData"]["data"])

def pcm_to_mp3(pcm, outpath):
    outpath.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-f","s16le","-ar","24000",
                    "-ac","1","-i","pipe:0","-b:a","64k","-y",str(outpath)],
                   input=pcm, check=True)

def main():
    items = collect()
    todo = [it for it in items if FORCE or not it[2].exists()]
    if LIMIT: todo = todo[:LIMIT]
    print(f"[plan] 대상 {len(items)}개(단어+예문) · 생성 필요 {len(todo)}개 · voice={VOICE} model={MODEL}")
    print(f"  GEMINI_API_KEY={'OK' if KEY else 'MISSING'}  출력=audio/w, audio/s")
    if not GO:
        print("\n(dry-run) 실제 생성은 --go. 예: python3 tools/gen_audio.py --go --limit 6")
        return
    if not KEY or "여기에" in KEY or any(ord(c)>127 for c in KEY):
        print("ERROR: GEMINI_API_KEY 환경변수에 실제 키를 넣어주세요"); sys.exit(1)
    ok=fail=0
    for i,(kind,text,outp) in enumerate(todo,1):
        try:
            pcm = tts(text); pcm_to_mp3(pcm, outp); ok+=1
            if i%25==0 or i==len(todo): print(f"  {i}/{len(todo)}  ({kind}) {outp.name}")
            time.sleep(0.4)   # rate limit 여유
        except urllib.error.HTTPError as e:
            fail+=1; print(f"  FAIL {outp.name}: HTTP {e.code} {e.read()[:200]}"); time.sleep(2)
        except Exception as e:
            fail+=1; print(f"  FAIL {outp.name}: {e}"); time.sleep(1)
    print(f"\n완료. 생성 {ok} · 실패 {fail}. audio/ 를 커밋하면 앱이 재생합니다.")

if __name__ == "__main__":
    main()
