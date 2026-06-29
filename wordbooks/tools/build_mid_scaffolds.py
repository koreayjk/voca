#!/usr/bin/env python3
"""
중등 단어장 스캐폴드 빌더 (corpus 불필요 — 예문은 콘텐츠 단계에서 자작).
입력: mid-pool.json ([{en,pos,ko,cefr,dom}])  ※수능과 중복 허용(중등은 별개 단계)
정책: 중등 3권끼리만 중복 제거(풀 이미 dedup) · 수능 중복 허용
선정: CEFR 밴드별로 영역(domain) 라운드로빈 → 모든 주제 균형 + 핵심우선(영역 내 생성순)
분할: mid1 기초 500(A1) / mid2 핵심 600(A1잔여+A2) / mid3 완성 700(B1) = 1,800
각 권은 영역순(주제별)으로 정렬 후 40개씩 Day 청크 → suneung-<prefix>-day<N>.scaffold.json
사용: build_mid_scaffolds.py [mid-pool.json]
"""
import json, sys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
PER = 40

POOLF = sys.argv[1] if len(sys.argv) > 1 else "mid-pool.json"
pool = json.load(open(ROOT / POOLF))
if isinstance(pool, dict):
    pool = pool.get("pool") or pool.get("words")

def valid(en):
    return bool(re.fullmatch(r"[a-z][a-z '\-]*[a-z]", en or ""))

# 정규화 + 중등 내부 중복 제거 + 원래 등장순(영역 내 핵심우선) 보존
seen = set(); clean = []
for i, w in enumerate(pool):
    en = (w.get("en") or "").lower().strip()
    if en in seen or not valid(en):
        continue
    seen.add(en)
    clean.append({"en": en, "pos": w.get("pos", ""), "ko": w.get("ko", ""),
                  "cefr": w.get("cefr", "A2"), "dom": w.get("dom", 99), "_i": i})

bands = {"A1": [], "A2": [], "B1": []}
for w in clean:
    bands.get(w["cefr"], bands["A2"]).append(w)
print(f"풀 {len(clean)}개 · A1={len(bands['A1'])} A2={len(bands['A2'])} B1={len(bands['B1'])}")

def roundrobin(words, n):
    """영역별로 한 개씩 번갈아 뽑아 n개 (각 영역 핵심우선=생성순). 반환:(선택, 잔여)"""
    from collections import OrderedDict, deque
    groups = OrderedDict()
    for w in words:
        groups.setdefault(w["dom"], deque()).append(w)
    picked = []
    qs = list(groups.values())
    while len(picked) < n and any(qs):
        for q in qs:
            if q:
                picked.append(q.popleft())
                if len(picked) >= n:
                    break
    chosen_ids = {id(w) for w in picked}
    rest = [w for w in words if id(w) not in chosen_ids]
    return picked, rest

# 밴드별 선정
a1_m1, a1_rest = roundrobin(bands["A1"], 500)        # mid1 = A1 500
a2_pick, _ = roundrobin(bands["A2"], 600 - len(a1_rest))  # mid2 A2분
b1_pick, _ = roundrobin(bands["B1"], 700)            # mid3 = B1 700

BOOKS = [
    ("mid1", "중등 기초", "MID-1", a1_m1),
    ("mid2", "중등 핵심", "MID-2", a1_rest + a2_pick),
    ("mid3", "중등 완성", "MID-3", b1_pick),
]

for prefix, title, code, words in BOOKS:
    words = sorted(words, key=lambda w: (w["dom"], w["_i"]))  # 주제별 정렬
    daynum = 1; bucket = []
    cef = {}
    for w in words:
        cef[w["cefr"]] = cef.get(w["cefr"], 0) + 1
    for i, w in enumerate(words):
        bucket.append({
            "en": w["en"], "ipa": "", "pos": w["pos"],
            "meanings": [{"pos": w["pos"], "ko": w["ko"], "ex": "", "tr": "", "src": ""}],
            "syn": [], "deriv": [], "roots": [], "etymHint": "", "level": w["cefr"],
            "exam": {"tested": False, "count": 0, "exams": 0, "recentYear": "", "stars": 0},
            "_ref": "",
        })
        if len(bucket) == PER or i == len(words) - 1:
            out = {"book": title, "code": code, "day": daynum, "words": bucket}
            json.dump(out, open(ROOT / f"suneung-{prefix}-day{daynum}.scaffold.json", "w"),
                      ensure_ascii=False, indent=1)
            bucket = []; daynum += 1
    print(f"{title}({prefix}): {len(words)}개 · {daynum-1}일 · CEFR {cef}")
