#!/usr/bin/env python3
"""회차 골고루 분산: 40단어에 서로 다른 기출 시험을 배정(전 연도 균등) + 깨끗한 실제 문장 선택."""
import json, re
from pathlib import Path
CORPUS = Path(__file__).resolve().parent.parent / "corpus"
occ = json.load(open(CORPUS/"occurrences.json"))

import re as _re
def good(s):
    if "____" in s or " / " in s: return False
    if s[0].islower(): return False
    n=len(s.split()); return 7 <= n <= 28

def exact(s, w):
    # 정확한 단어 또는 흔한 굴절형이 등장하는지
    return bool(_re.search(r"\b"+_re.escape(w)+r"(s|es|ed|d|ing|al|ally|ly|ity|ies)?\b", s, _re.I))

# 사용 가능한 전체 시험 라벨 풀(모든 단어 후보에서 등장한 것)
all_labels = sorted({c["label"] for w in occ for c in occ[w]["cands"]},
                    key=lambda L:(int(L.split()[0]), L.split()[1]))

# 그리디: 후보 시험수 적은 단어부터, 아직 안 쓴 label 중 '깨끗한 문장' 우선
words = sorted(occ.keys(), key=lambda w: occ[w]["exams"])
used=set(); result={}
for w in words:
    cands = occ[w]["cands"]
    fresh = [c for c in cands if c["label"] not in used]
    pool = fresh or cands
    # 우선순위: 미사용 & 깨끗 & 정확단어 > 미사용 & 깨끗 > 미사용 > 나머지
    def rank(c):
        return (good(c["sentence"]), exact(c["sentence"], w))
    pick = max(pool, key=rank)
    used.add(pick["label"]); result[w]=pick

for w in occ.keys():
    p=result[w]
    print(f"\n### {w}  —  [{p['label']} {p['item']}번]")
    print(f"   {p['sentence']}")
print(f"\n\n사용 시험 {len(used)}종 / 가용 {len(all_labels)}종")
print("연도분포:", sorted({L.split()[0] for L in used}))
Path(CORPUS/"assigned.json").write_text(json.dumps(result,ensure_ascii=False,indent=1),encoding="utf-8")
