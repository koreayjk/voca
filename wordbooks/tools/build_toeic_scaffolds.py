#!/usr/bin/env python3
"""
TOEIC 빈출 풀(toeic-pool-full.json) → 빈도 난이도 3권 스캐폴드.
tier: 최빈출→기초, 다음→핵심, 그 다음(희귀·고난도)→고득점. (권 간 중복 없음)
예문은 콘텐츠 단계에서 자작(비즈니스 상황) — corpus 원문 인용/출처 없음.
출력: suneung-<prefix>-day<N>.scaffold.json (prefix=toeic1/toeic2/toeic3), 40개/Day
사용: build_toeic_scaffolds.py [기초 핵심 고득점]  (기본 500 700 900)
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
PER = 40
N1 = int(sys.argv[1]) if len(sys.argv) > 1 else 500
N2 = int(sys.argv[2]) if len(sys.argv) > 2 else 700
N3 = int(sys.argv[3]) if len(sys.argv) > 3 else 900

pool = json.load(open(ROOT / "toeic-pool-full.json"))["words"]
# 빈도순 이미 정렬됨. 안전하게 재정렬.
pool.sort(key=lambda x: (-x["exams"], -x["total"]))
words = [p["w"] for p in pool]
need = N1 + N2 + N3
if len(words) < need:
    print(f"⚠️ 풀 부족: {len(words)} < {need}")

# 등급 라벨(빈도 기반, 목표점수 느낌)
def lvl(prefix):
    return {"toeic1": "600", "toeic2": "800", "toeic3": "900"}[prefix]

BOOKS = [
    ("toeic1", "토익 기초", "TOEIC-1", words[:N1]),
    ("toeic2", "토익 핵심", "TOEIC-2", words[N1:N1+N2]),
    ("toeic3", "토익 고득점", "TOEIC-3", words[N1+N2:N1+N2+N3]),
]
star = {p["w"]: p for p in pool}

for prefix, title, code, chunk in BOOKS:
    daynum = 1; bucket = []
    for i, w in enumerate(chunk):
        sm = star[w]
        bucket.append({
            "en": w, "ipa": "", "pos": "",
            "meanings": [{"pos": "", "ko": "", "ex": "", "tr": "", "src": ""}],
            "syn": [], "deriv": [], "roots": [], "etymHint": "", "level": lvl(prefix),
            "exam": {"tested": True, "count": sm["total"], "exams": sm["exams"],
                     "recentYear": "", "stars": sm["stars"]},
            "_ref": "",
        })
        if len(bucket) == PER or i == len(chunk) - 1:
            out = {"book": title, "code": code, "day": daynum, "words": bucket}
            json.dump(out, open(ROOT / f"suneung-{prefix}-day{daynum}.scaffold.json", "w"),
                      ensure_ascii=False, indent=1)
            bucket = []; daynum += 1
    print(f"{title}({prefix}): {len(chunk)}개 · {daynum-1}일 ({chunk[0]}…{chunk[-1]})")
print("권 간 중복: 0 (빈도순 순차 분할)")
