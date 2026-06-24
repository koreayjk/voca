#!/usr/bin/env python3
"""
공식 단어장(수능 기본 Day1~30)을 Supabase voca_books/voca_pages/voca_words 에 시드.
- REST API + service_role 키 사용(RLS 우회). 멱등: 같은 코드의 공식책 있으면 --reset 으로 재시드.
- 매핑: en/ipa/level 그대로, base=주뜻, ctx=보조뜻, sentence=영어예문,
        analysis={synonyms,example,example_kr + 보존필드(deriv/etym/roots/exam/src)}.

실행:
  export SB_URL="https://xxxx.supabase.co"
  export SB_SERVICE_KEY="<service_role 키>"      # ⚠️ 비공개. 절대 커밋/공유 금지
  export OFFICIAL_OWNER="<voca_books.user_id 로 쓸 멤버 uuid>"  # 시스템/관리자 계정
  python3 seed_official.py            # 미리보기(dry-run)
  python3 seed_official.py --go       # 실제 시드
  python3 seed_official.py --go --reset   # 기존 공식책 삭제 후 재시드
선행: supabase/official-books.sql 을 먼저 실행해 is_official 컬럼/RLS 생성.
"""
import os, sys, json, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SB_URL = os.environ.get("SB_URL", "").rstrip("/")
KEY = os.environ.get("SB_SERVICE_KEY", "")
OWNER = os.environ.get("OFFICIAL_OWNER", "")
GO = "--go" in sys.argv
RESET = "--reset" in sys.argv

BOOK_TITLE = "수능 기본"
BOOK_CODE = "SUN-BASIC"        # description 에 저장(식별용)
DAYS = list(range(1, 31))

def req(method, path, body=None, prefer=None):
    url = SB_URL + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("apikey", KEY); r.add_header("Authorization", "Bearer " + KEY)
    r.add_header("Content-Type", "application/json")
    if prefer: r.add_header("Prefer", prefer)
    with urllib.request.urlopen(r) as resp:
        txt = resp.read().decode()
        return json.loads(txt) if txt else None

def map_word(w):
    m = w.get("meanings", []); m0 = m[0] if m else {}
    base = (m0.get("ko", "") or "").strip()
    ctx = " · ".join(mm.get("ko", "") for mm in m[1:] if mm.get("ko"))
    analysis = {
        "synonyms": w.get("syn", []),
        "example": m0.get("ex", ""),
        "example_kr": m0.get("tr", ""),
        # 보존(현재 미렌더, 추후 공식카드 확장용)
        "_official": True, "src": m0.get("src", ""),
        "deriv": w.get("deriv", []), "etym": w.get("etymHint", ""),
        "roots": w.get("roots", []), "exam": w.get("exam"),
    }
    return {"en": w["en"], "ipa": w.get("ipa", ""), "base": base, "ctx": ctx,
            "sentence": m0.get("ex", ""), "level": w.get("level", ""), "analysis": analysis}

def load_days():
    out = []
    for n in DAYS:
        d = json.load(open(ROOT / f"suneung-basic-day{n}.json"))
        out.append((f"Day {n}", [map_word(w) for w in d["words"]]))
    return out

def find_official():
    q = f"/rest/v1/voca_books?is_official=eq.true&description=eq.{urllib.parse.quote(BOOK_CODE)}&select=id&limit=1"
    r = req("GET", q)
    return (r[0]["id"] if r else None)

def delete_book(bid):
    pages = req("GET", f"/rest/v1/voca_pages?book_id=eq.{bid}&select=id") or []
    for p in pages:
        req("DELETE", f"/rest/v1/voca_words?page_id=eq.{p['id']}")
    req("DELETE", f"/rest/v1/voca_pages?book_id=eq.{bid}")
    req("DELETE", f"/rest/v1/voca_books?id=eq.{bid}")

def main():
    days = load_days()
    total = sum(len(ws) for _, ws in days)
    print(f"[plan] {BOOK_TITLE}({BOOK_CODE}) · {len(days)} pages · {total} words")
    print(f"  SB_URL={'OK' if SB_URL else 'MISSING'}  KEY={'OK' if KEY else 'MISSING'}  OWNER={'OK' if OWNER else 'MISSING'}")
    print("  sample word:", json.dumps(map_word(json.load(open(ROOT/'suneung-basic-day1.json'))['words'][0]), ensure_ascii=False)[:200])
    if not GO:
        print("\n(dry-run) 실제 시드는 --go 를 붙이세요. 선행: official-books.sql 실행.")
        return
    if not (SB_URL and KEY and OWNER):
        print("ERROR: SB_URL / SB_SERVICE_KEY / OFFICIAL_OWNER 환경변수 필요"); sys.exit(1)
    # placeholder/한글 감지 (안내문을 그대로 export 한 경우)
    bad = [n for n, v in [("SB_SERVICE_KEY", KEY), ("OFFICIAL_OWNER", OWNER)]
           if ("여기에" in v) or any(ord(c) > 127 for c in v)]
    if bad:
        print(f"ERROR: {', '.join(bad)} 에 실제 값이 안 들어갔어요(안내문/한글 감지).")
        print("  SB_SERVICE_KEY = Supabase 대시보드 Settings→API→service_role 키 (eyJ... 로 시작)")
        print("  OFFICIAL_OWNER = members 테이블의 본인 계정 id (uuid)")
        sys.exit(1)
    import re as _re
    if not _re.fullmatch(r"[0-9a-fA-F-]{32,40}", OWNER):
        print(f"ERROR: OFFICIAL_OWNER 가 uuid 형식이 아니에요: {OWNER!r}"); sys.exit(1)

    existing = find_official()
    if existing and not RESET:
        print(f"이미 공식책 존재(id={existing}). 재시드하려면 --reset. 중단."); return
    if existing and RESET:
        print(f"기존 공식책 삭제 중(id={existing})..."); delete_book(existing)

    book = req("POST", "/rest/v1/voca_books",
               {"user_id": OWNER, "title": BOOK_TITLE, "author": "IM VOCA",
                "color": "#1c3553", "description": BOOK_CODE, "is_official": True},
               prefer="return=representation")
    bid = (book[0] if isinstance(book, list) else book)["id"]
    print(f"book 생성 id={bid}")
    for page_num, words in days:
        pg = req("POST", "/rest/v1/voca_pages", {"book_id": bid, "page_num": page_num},
                 prefer="return=representation")
        pid = (pg[0] if isinstance(pg, list) else pg)["id"]
        rows = [{**w, "page_id": pid} for w in words]
        saved = req("POST", "/rest/v1/voca_words", rows, prefer="return=representation")
        print(f"  {page_num}: {len(saved) if isinstance(saved,list) else '?'} words")
    print(f"\n완료. 공식책 uuid = {bid}  (배정/리포트가 이 uuid로 동작)")

if __name__ == "__main__":
    main()
