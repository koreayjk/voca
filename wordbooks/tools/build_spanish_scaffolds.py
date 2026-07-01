#!/usr/bin/env python3
"""
스페인어 단어장 스캐폴드 빌더 (corpus 불필요, 회화 예문은 콘텐츠 단계에서 자작).
입력: spa-gen-pool.json (일상 [{es,pos,gen,ko,level,track,dom}]) + spa-mis-pool.json (선교)
정책: 기초↔중급 중복 없음 / 선교는 중복 허용(별도 풀)
선정: 일상 = CEFR 밴드별 영역 라운드로빈 → 기초 500(A1+쉬운A2) / 중급 600(A2+B1)
      선교 = 주제순 상위 N (기본 400)
출력: suneung-<prefix>-day<N>.scaffold.json (prefix=esp1/esp2/esp3), 40개/Day
사용: build_spanish_scaffolds.py [기초수 중급수 선교수]
"""
import json, sys, re
from pathlib import Path
from collections import OrderedDict, deque
ROOT = Path(__file__).resolve().parent.parent
PER = 40
N1 = int(sys.argv[1]) if len(sys.argv) > 1 else 500
N2 = int(sys.argv[2]) if len(sys.argv) > 2 else 600
N3 = int(sys.argv[3]) if len(sys.argv) > 3 else 400

gen = json.load(open(ROOT / "spa-gen-pool.json"))
mis = json.load(open(ROOT / "spa-mis-pool.json"))

def dedup(rows):
    seen = set(); out = []
    for i, w in enumerate(rows):
        k = (w.get("es") or "").lower().strip()
        if not k or k in seen: continue
        seen.add(k); out.append({**w, "es": k, "_i": i})
    return out

gen = dedup(gen); mis = dedup(mis)

def roundrobin(words, n):
    groups = OrderedDict()
    for w in words: groups.setdefault(w.get("dom", 0), deque()).append(w)
    picked = []; qs = list(groups.values())
    while len(picked) < n and any(qs):
        for q in qs:
            if q: picked.append(q.popleft())
            if len(picked) >= n: break
    ids = {id(w) for w in picked}
    return picked, [w for w in words if id(w) not in ids]

# 일상: 밴드별
A1 = [w for w in gen if w["level"] == "A1"]
A2 = [w for w in gen if w["level"] == "A2"]
B1 = [w for w in gen if w["level"] == "B1"]
b1_book, a1_rest = roundrobin(A1, N1)              # 기초 = A1 라운드로빈
need2 = N2 - len(a1_rest)
a2_pick, a2_rest = roundrobin(A2, max(0, need2))   # 중급 = A1잔여 + A2(+B1 보충)
mid_words = a1_rest + a2_pick
if len(mid_words) < N2:
    b1_pick, _ = roundrobin(B1, N2 - len(mid_words)); mid_words += b1_pick
mis_book, _ = roundrobin(mis, N3)

BOOKS = [
    ("esp1", "스페인어 기초", "ESP-1", b1_book, "dom"),
    ("esp2", "스페인어 중급", "ESP-2", mid_words, "dom"),
    ("esp3", "스페인어 선교", "ESP-3", mis_book, "dom"),
]

for prefix, title, code, words, sortkey in BOOKS:
    words = sorted(words, key=lambda w: (w.get("dom", 0), w.get("_i", 0)))
    daynum = 1; bucket = []
    from collections import Counter
    cef = Counter(w["level"] for w in words)
    for i, w in enumerate(words):
        pos = w.get("pos", "")
        # 명사는 뜻 앞에 성 표시 힌트 유지(콘텐츠가 el/la 반영)
        bucket.append({
            "en": w["es"], "ipa": "", "pos": pos, "gen": w.get("gen", ""),
            "meanings": [{"pos": pos, "ko": w.get("ko", ""), "ex": "", "tr": "", "src": ""}],
            "syn": [], "deriv": [], "roots": [], "etymHint": "", "level": w.get("level", ""),
            "exam": {"tested": False, "count": 0, "exams": 0, "recentYear": "", "stars": 0},
            "_ref": "",
        })
        if len(bucket) == PER or i == len(words) - 1:
            out = {"book": title, "code": code, "day": daynum, "words": bucket}
            json.dump(out, open(ROOT / f"suneung-{prefix}-day{daynum}.scaffold.json", "w"),
                      ensure_ascii=False, indent=1)
            bucket = []; daynum += 1
    print(f"{title}({prefix}): {len(words)}개 · {daynum-1}일 · CEFR {dict(cef)}")

# 중복 점검(기초↔중급)
s1 = {w["es"] for w in b1_book}; s2 = {w["es"] for w in mid_words}
print(f"기초↔중급 중복: {len(s1 & s2)}  (선교는 중복 허용)")
