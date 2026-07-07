#!/usr/bin/env python3
"""
학생 한 명의 학습·복습 활동 상세 덤프 (점수 폭증 원인 진단용).
- 본인 책 vs 공식책, 학습(복습등록) 페이지 수, 복습 완료/진행, is_perfect(제때) 비율,
  첫암기 점수 vs 복습단계 점수 추정.
env: SB_URL, SB_SERVICE_KEY   실행: python3 tools/inspect_student.py "한필립"
"""
import os, sys, json, urllib.request, urllib.error, urllib.parse
SB_URL = os.environ.get("SB_URL", "https://ziatqkjlafucqtwshhla.supabase.co").rstrip("/")
KEY = os.environ.get("SB_SERVICE_KEY", "")
NAME = os.environ.get("STUDENT_NAME") or (sys.argv[1] if len(sys.argv) > 1 else "")
WEIGHTS = {"A2": 1, "B1": 2, "B2": 3, "C1": 4, "C2": 5}
STEPKEYS = ["review_2d", "review_3d", "review_6d", "review_15d", "review_30d", "review_60d"]

def req(path):
    r = urllib.request.Request(SB_URL + path)
    r.add_header("apikey", KEY); r.add_header("Authorization", "Bearer " + KEY)
    try:
        with urllib.request.urlopen(r, timeout=60) as x: return json.load(x)
    except urllib.error.HTTPError as e: return {"err": e.code, "body": e.read()[:200].decode(errors="ignore")}

_pc = {}
def page_info(book_id, page_num):
    k = (book_id, str(page_num))
    if k in _pc: return _pc[k]
    pages = req(f"/rest/v1/voca_pages?book_id=eq.{book_id}&page_num=eq.{urllib.parse.quote(str(page_num))}&select=id")
    sc = wc = 0
    if isinstance(pages, list) and pages:
        ws = req(f"/rest/v1/voca_words?page_id=eq.{pages[0]['id']}&select=level")
        if isinstance(ws, list):
            wc = len(ws); sc = sum(WEIGHTS.get(w.get("level"), 1) for w in ws)
    _pc[k] = (sc, wc); return _pc[k]

def main():
    if not KEY: print("SB_SERVICE_KEY 필요"); sys.exit(1)
    if not NAME: print("학생 이름 인자 필요"); sys.exit(1)
    ms = req("/rest/v1/members?name=eq." + urllib.parse.quote(NAME) + "&select=id,name,total_words,perfect_reviews,scan_count,visit_count&order=perfect_reviews.desc")
    if not isinstance(ms, list) or not ms: print("학생 없음:", ms); return
    m = ms[0]
    print(f"=== {m['name']} ===  perfect_reviews={m.get('perfect_reviews')}  total_words={m.get('total_words')}  scan={m.get('scan_count')}  방문={m.get('visit_count')}")
    # 책 제목 캐시 (공식/본인 구분)
    obooks = {b["id"]: b for b in (req(f"/rest/v1/voca_books?is_official=eq.true&select=id,title") or [])}
    mybooks = {b["id"]: b for b in (req(f"/rest/v1/voca_books?user_id=eq.{m['id']}&select=id,title") or [])}
    revs = req(f"/rest/v1/voca_review?user_id=eq.{m['id']}&select=book_id,page_num,completed,is_perfect,{','.join(STEPKEYS)},first_studied_at")
    if not isinstance(revs, list): print("voca_review 조회 실패:", revs); return
    print(f"학습(복습등록)한 페이지: {len(revs)}개")
    off_pages = own_pages = 0
    first_pts = review_pts = 0
    completed = perfect_cnt = 0
    step_total = 0
    for r in revs:
        bid = r["book_id"]; title = (obooks.get(bid) or mybooks.get(bid) or {}).get("title", "?")
        is_official = bid in obooks
        sc, wc = page_info(bid, r["page_num"])
        if is_official: off_pages += 1
        else: own_pages += 1
        first_pts += sc                                   # 첫암기 1회분
        done_steps = sum(1 for kk in STEPKEYS if r.get(kk) is None)  # null=완료한 단계
        step_total += done_steps
        review_pts += done_steps * sc                     # (근사: 완주 2배 보너스는 미반영)
        if r.get("completed"): completed += 1
        if r.get("is_perfect"): perfect_cnt += 1
    print(f"  · 공식책 페이지 {off_pages} · 본인책 페이지 {own_pages}")
    print(f"  · 복습 완주(completed) {completed} · is_perfect(제때) {perfect_cnt}/{len(revs)}")
    print(f"  · 완료한 복습 단계 총합 {step_total} (평균 {step_total/max(1,len(revs)):.1f}단계/페이지)")
    print(f"[점수 추정] 첫암기≈{first_pts} · 복습단계≈{review_pts} · 합≈{first_pts+review_pts} (실제 perfect_reviews={m.get('perfect_reviews')})")
    # 페이지 많이 등록한 책 top
    from collections import Counter
    bc = Counter((obooks.get(r['book_id']) or mybooks.get(r['book_id']) or {}).get('title','?') for r in revs)
    print("[책별 학습 페이지 수] " + ", ".join(f"{t}:{n}" for t, n in bc.most_common(10)))

if __name__ == "__main__":
    main()
