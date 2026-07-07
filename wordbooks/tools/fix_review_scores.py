#!/usr/bin/env python3
"""
명예의 전당 점수 정정: 각 학생의 perfect_reviews 에서 '첫 암기(첫 학습)로 받은 점수'만 차감.
- 첫 암기 점수 = 그 학생이 학습한(=voca_review 에 등록된) 각 페이지의 calcWordScore 합.
  calcWordScore: 페이지 단어들의 CEFR 가중치 합(A2=1·B1=2·B2=3·C1=4·C2=5, 그 외=1).
- new = max(0, perfect_reviews - 첫암기점수합).  실제 복습(간격 복습)으로 받은 점수는 보존.
- RLS 우회를 위해 service_role 키 필요.
⚠️ 한 번만 실행(멱등 아님 — 두 번 실행하면 또 차감됨). 먼저 dry-run 으로 확인 후 --go.

env: SB_URL, SB_SERVICE_KEY   실행: python3 tools/fix_review_scores.py [--go]
"""
import os, sys, json, urllib.request, urllib.error

SB_URL = os.environ.get("SB_URL", "https://ziatqkjlafucqtwshhla.supabase.co").rstrip("/")
KEY = os.environ.get("SB_SERVICE_KEY", "")
GO = "--go" in sys.argv
WEIGHTS = {"A2": 1, "B1": 2, "B2": 3, "C1": 4, "C2": 5}

def req(method, path, body=None):
    r = urllib.request.Request(SB_URL + path, method=method,
        data=json.dumps(body).encode() if body is not None else None)
    r.add_header("apikey", KEY); r.add_header("Authorization", "Bearer " + KEY)
    r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            t = x.read().decode()
            return json.loads(t) if t.strip() else []
    except urllib.error.HTTPError as e:
        return {"err": e.code, "body": e.read()[:200].decode(errors="ignore")}

_page_cache = {}
def page_score(book_id, page_num):
    k = (book_id, str(page_num))
    if k in _page_cache: return _page_cache[k]
    pages = req("GET", f"/rest/v1/voca_pages?book_id=eq.{book_id}&page_num=eq.{urllib.parse.quote(str(page_num))}&select=id")
    sc = 0
    if isinstance(pages, list) and pages:
        pid = pages[0]["id"]
        words = req("GET", f"/rest/v1/voca_words?page_id=eq.{pid}&select=level")
        if isinstance(words, list):
            sc = sum(WEIGHTS.get(w.get("level"), 1) for w in words)
    _page_cache[k] = sc
    return sc

import urllib.parse
def main():
    if not KEY or any(ord(c) > 127 for c in KEY):
        print("ERROR: SB_SERVICE_KEY 환경변수에 실제 service_role 키 필요"); sys.exit(1)
    members = req("GET", "/rest/v1/members?select=id,name,perfect_reviews&perfect_reviews=gt.0&order=perfect_reviews.desc")
    if not isinstance(members, list):
        print("members 조회 실패:", members); sys.exit(1)
    print(f"[plan] 대상 학생 {len(members)}명 · {'적용(--go)' if GO else 'DRY-RUN(미적용)'}\n")
    print(f"{'이름':<12} {'현재':>8} {'첫암기차감':>10} {'→ 정정후':>9}")
    changed = 0
    for m in members:
        revs = req("GET", f"/rest/v1/voca_review?user_id=eq.{m['id']}&select=book_id,page_num")
        first = 0
        if isinstance(revs, list):
            for rv in revs:
                first += page_score(rv["book_id"], rv["page_num"])
        cur = m.get("perfect_reviews", 0) or 0
        new = max(0, cur - first)
        print(f"{(m.get('name') or '?'):<12} {cur:>8} {first:>10} {new:>9}")
        if GO and new != cur:
            r = req("PATCH", f"/rest/v1/members?id=eq.{m['id']}", {"perfect_reviews": new})
            if isinstance(r, dict) and r.get("err"): print("  PATCH 실패:", r)
            else: changed += 1
    print(f"\n{'적용 완료: ' + str(changed) + '명 수정' if GO else 'DRY-RUN. 실제 반영은 --go'}")

if __name__ == "__main__":
    main()
