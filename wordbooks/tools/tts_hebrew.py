#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""히브리어 음원 만들기 — Google Cloud TTS(he-IL) → Supabase Storage(audio 버킷).

왜 따로 만드나:
  edge function 의 tts 는 영어 전용이다(VOICE 가 en-US 고정, 파일명도 ASCII 기준).
  히브리어는 22자뿐이고 한 번 만들면 끝이라, 런타임 경로를 건드리지 않고
  여기서 한 번 돌려 올린다.

무엇을 읽는가:
  · 글자 발음(w) = 글자 '이름'  (예: 'א' 가 아니라 'אָלֶף')
      → audio/he/w/alef.mp3        앱: 카드 앞면 발음 버튼
  · 예시 발음(s) = 예시 단어      (예: 'אָב')
      → audio/he/s/alef_<해시>.mp3  앱: 카드 뒷면 자동 읽기
  해시는 앱 _sentHash 와 같은 알고리즘이다(djb2-xor, base36). 예문 글자가
  하나라도 바뀌면 해시가 달라져 옛 파일을 찾지 않는다 = 불일치 원천 차단.

비용:
  22자 이름 + 22개 예시 단어 ≈ 300자. WaveNet 은 월 100만 자 무료다.

실행(터미널):
  export SB_URL="https://xxxx.supabase.co"
  export SB_SERVICE_KEY="..."        # ⚠️ 비공개. 커밋·공유 금지
  export GOOGLE_TTS_KEY="..."        # ⚠️ 비공개
  python3 tts_hebrew.py              # 미리보기(만들 목록만)
  python3 tts_hebrew.py --go         # 실제 생성·업로드
옵션:
  --force      이미 있는 파일도 다시 만든다 (기본은 건너뜀)
  --words-only 글자 이름만 (예시 단어 음원 생략)
"""
import os, sys, json, glob, base64, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SB_URL = os.environ.get("SB_URL", "").rstrip("/")
SB_KEY = os.environ.get("SB_SERVICE_KEY", "")
GKEY = os.environ.get("GOOGLE_TTS_KEY", "")
VOICE = os.environ.get("HE_TTS_VOICE", "he-IL-Wavenet-A")
LANG = "he-IL"
BUCKET = "audio"
NS = "he"

GO = "--go" in sys.argv
FORCE = "--force" in sys.argv
WORDS_ONLY = "--words-only" in sys.argv


def sent_hash(s):
    """앱 _sentHash 와 동일: djb2-xor, unsigned 32bit, base36."""
    s = (s or "").strip()
    h = 5381
    for ch in s:
        h = ((h * 33) ^ ord(ch)) & 0xFFFFFFFF
    if h == 0:
        return "0"
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    out = ""
    while h:
        out = digits[h % 36] + out
        h //= 36
    return out


def synth(text):
    """Google TTS → mp3 바이트."""
    body = json.dumps({
        "input": {"text": text},
        "voice": {"languageCode": LANG, "name": VOICE},
        # speakingRate 0.85 — 글자 이름은 짧아서 기본 속도면 훅 지나간다
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": 0.85},
    }).encode()
    r = urllib.request.Request(
        "https://texttospeech.googleapis.com/v1/text:synthesize?key=" + GKEY,
        data=body, method="POST")
    r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=60) as resp:
        return base64.b64decode(json.loads(resp.read().decode())["audioContent"])


def exists(path):
    r = urllib.request.Request(f"{SB_URL}/storage/v1/object/public/{BUCKET}/{path}", method="HEAD")
    try:
        with urllib.request.urlopen(r, timeout=20):
            return True
    except urllib.error.HTTPError:
        return False
    except Exception:
        return False


def upload(path, mp3):
    r = urllib.request.Request(f"{SB_URL}/storage/v1/object/{BUCKET}/{path}", data=mp3, method="POST")
    r.add_header("Authorization", "Bearer " + SB_KEY)
    r.add_header("apikey", SB_KEY)
    r.add_header("Content-Type", "audio/mpeg")
    r.add_header("x-upsert", "true")
    r.add_header("Cache-Control", "public, max-age=31536000, immutable")
    with urllib.request.urlopen(r, timeout=60) as resp:
        return resp.status


def jobs():
    """(저장경로, 읽을 글자, 설명) 목록."""
    out = []
    files = sorted(glob.glob(str(ROOT / "hebrew" / "hebrew-alefbet-day*.json")))
    if not files:
        print("ERROR: hebrew/hebrew-alefbet-day*.json 이 없어요. build-alefbet.py 를 먼저 돌리세요.")
        sys.exit(1)
    for f in files:
        for w in json.load(open(f, encoding="utf-8"))["words"]:
            key = w.get("audio", "")
            name = w.get("ttsName", "")
            if not key or not name:
                print(f"  (skip) audio/ttsName 없음: {w.get('en')!r}")
                continue
            out.append((f"{NS}/w/{key}.mp3", name, f"{w['en']} 이름 {name}"))
            if WORDS_ONLY:
                continue
            ex = (w["meanings"][0].get("ex") or "").strip()
            if ex:
                out.append((f"{NS}/s/{key}_{sent_hash(ex)}.mp3", ex, f"{w['en']} 예시 {ex}"))
    return out


def main():
    js = jobs()
    chars = sum(len(t) for _, t, _ in js)
    print(f"[plan] {len(js)}개 파일 · {chars}자 · voice={VOICE}")
    print(f"  SB_URL={'OK' if SB_URL else 'MISSING'}  SB_SERVICE_KEY={'OK' if SB_KEY else 'MISSING'}  GOOGLE_TTS_KEY={'OK' if GKEY else 'MISSING'}")
    for path, text, desc in js[:4]:
        print(f"  {path}  ←  {desc}")
    if len(js) > 4:
        print(f"  … 외 {len(js)-4}개")
    if not GO:
        print("\n(dry-run) 실제 생성·업로드는 --go")
        return
    if not (SB_URL and SB_KEY and GKEY):
        print("ERROR: SB_URL / SB_SERVICE_KEY / GOOGLE_TTS_KEY 환경변수 필요")
        sys.exit(1)
    made = skipped = failed = 0
    for path, text, desc in js:
        if not FORCE and exists(path):
            skipped += 1
            print(f"  (있음) {path}")
            continue
        try:
            upload(path, synth(text))
            made += 1
            print(f"  ✓ {path}  ←  {desc}")
        except urllib.error.HTTPError as e:
            failed += 1
            print(f"  ✗ {path}  {e.code} {e.read().decode()[:200]}")
        except Exception as e:
            failed += 1
            print(f"  ✗ {path}  {e}")
    print(f"\n완료. 생성 {made} · 건너뜀 {skipped} · 실패 {failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
