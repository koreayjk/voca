#!/usr/bin/env python3
"""
Day 스캐폴드 빌더.
- 이미 만든 Day JSON들(suneung-basic-day*.json)에서 사용 단어 수집 → 중복 제외
- suneung-selection.json을 (stars desc, exams desc, total desc)로 정렬해 다음 40단어 선정
- find_occurrences 로직 재사용해 각 단어의 실제 기출 문장+출처 자동 배정(회차 골고루)
- 출력: suneung-basic-day<N>.scaffold.json  (en, exam stats, src, refSentence 포함; 언어정보는 빈칸)
사용: build_day.py <N>
"""
import json, sys, re, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
TESTDIR = (ROOT/".."/".."/"test").resolve()
CORPUS = ROOT/"corpus"
sys.path.insert(0, str(ROOT/"tools"))
from find_occurrences import stem_re, split_items, sentences  # 재사용

N = int(sys.argv[1])
PER_DAY = 40

# 1) 사용된 단어 수집
used = set()
for f in sorted(ROOT.glob("suneung-basic-day*.json")):
    if ".scaffold." in f.name: continue
    d = json.load(open(f))
    for w in d.get("words", []):
        used.add(w["en"].lower())

# 2) 선택 풀 정렬 → 다음 40 (기능어/기초어 스톱리스트 제외)
STOP = set()
for ln in (ROOT/"tools"/"stopwords.txt").read_text(encoding="utf-8").splitlines():
    ln=ln.split("#")[0].strip()
    for tok in ln.split(): STOP.add(tok.lower())
sel = json.load(open(ROOT/"suneung-selection.json"))["words"]
def keyf(w): return (-w["stars"], -w["exams"], -w["total"])
ordered = [w for w in sorted(sel, key=keyf) if w["w"].lower() not in used]
# 너무 짧거나(<=2) 굴절형 surface·스톱워드는 스킵
def ok(s):
    sl=s.lower()
    return (s.isalpha() and len(s) >= 3 and sl not in STOP
            and not s.endswith("ing") and not s.endswith("ed"))
pick = []
for w in ordered:
    if ok(w["w"]):
        pick.append(w)
    if len(pick) >= PER_DAY: break
words = [w["w"] for w in pick]

# 3) 코퍼스 로드 + 문항분리 (1회)
index = json.load(open(CORPUS/"index.json"))
exams = []
for row in index:
    raw = subprocess.run(["pdftotext","-raw",str(TESTDIR/row["file"]),"-"],
                         capture_output=True,text=True,timeout=60).stdout
    exams.append((row["label"], row.get("recentYear",row["year"]), split_items(raw)))

def good(s):
    if "____" in s or " / " in s: return False
    if s[0].islower(): return False
    n=len(s.split()); return 7 <= n <= 28
def exact(s,w):
    return bool(re.search(r"\b"+re.escape(w)+r"(s|es|ed|d|ing|al|ally|ly|ity|ies)?\b", s, re.I))

# 단어별 후보(라벨당 최고문장) + recentYear(등장 시험 중 최신연도)
cand = {}; recent = {}
for w in words:
    rx = stem_re(w); by={}; yrs=set()
    for label, ry, items in exams:
        for num,text in items.items():
            for s in sentences(text):
                if rx.search(s):
                    yrs.add(int(label.split()[0]))
                    sc=(good(s), exact(s,w), -abs(16-len(s.split())))
                    if label not in by or sc>by[label][0]:
                        by[label]=(sc,{"label":label,"item":num,"sentence":s})
    cand[w]=[v[1] for v in by.values()]
    recent[w]=str(max(yrs)) if yrs else ""

# 회차 골고루 그리디 배정 (희소단어 우선)
used_ex=set(); assign={}
for w in sorted(words, key=lambda w: len(cand[w])):
    pool = cand[w]
    fresh=[c for c in pool if c["label"] not in used_ex] or pool
    if not fresh:
        assign[w]=None; continue
    pick_c=max(fresh, key=lambda c:(good(c["sentence"]),exact(c["sentence"],w)))
    used_ex.add(pick_c["label"]); assign[w]=pick_c

# 4) 스캐폴드 출력
selmap={w["w"]:w for w in sel}
out={"book":"수능 기본","code":"SUN-BASIC","day":N,"words":[]}
for w in words:
    a=assign[w]; sm=selmap[w]
    out["words"].append({
        "en":w,"ipa":"","pos":"",
        "meanings":[{"pos":"","ko":"","ex":"","tr":"",
                     "src": f"{a['label']} {a['item']}번" if a else ""}],
        "syn":[],"deriv":[],"roots":[],"etymHint":"","level":"",
        "exam":{"tested":True,"count":sm["total"],"exams":sm["exams"],
                "recentYear":recent.get(w,""),"stars":sm["stars"]},
        "_ref": a["sentence"] if a else ""    # 재작성 참고용(완성 시 제거)
    })
p=ROOT/f"suneung-basic-day{N}.scaffold.json"
json.dump(out,open(p,"w"),ensure_ascii=False,indent=1)
print(f"Day{N} 스캐폴드 {len(words)}단어 → {p.name}")
print("배정 시험:", len({a['label'] for a in assign.values() if a}),"종")
for w in words:
    a=assign[w]
    print(f"  {w:14s} {sm if False else ''}[{(a['label']+' '+str(a['item'])+'번') if a else 'NONE'}]  {a['sentence'][:70] if a else ''}")
