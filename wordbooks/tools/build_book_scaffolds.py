#!/usr/bin/env python3
"""
범용 Day 스캐폴드 빌더 (기본 외 책 — 핵심/고난도/숙어).
suneung-pool-full.json 에서 이미 만든 모든 책 단어를 제외하고 다음 단어를 40개씩 Day로 청크,
각 단어에 회차 골고루 기출 출처 배정 + recentYear.

사용: build_book_scaffolds.py "<책이름>" <CODE> <prefix> <pool.json> <START> <END>
예:   build_book_scaffolds.py "수능 핵심" SUN-CORE core suneung-pool-full.json 1 45
출력: suneung-<prefix>-day<N>.scaffold.json  (gitignore — _ref 실문장 포함)
제외: suneung-*-day*.json (이미 만든 모든 책)
(corpus/ 필요 → 로컬에서만 실행)
"""
import json, sys, re, subprocess, glob
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
TESTDIR=(ROOT/".."/".."/"test").resolve()
CORPUS=ROOT/"corpus"
sys.path.insert(0,str(ROOT/"tools"))
from find_occurrences import stem_re, split_items, sentences

BOOK, CODE, PREFIX, POOLF, START, END = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6])
PER=40

# 이미 만든 모든 책(기본·핵심·이 책 기존분 등 전부) 단어 제외
used=set()
for fn in glob.glob(str(ROOT/"suneung-*-day*.json")):
    if ".scaffold." in fn: continue
    for w in json.load(open(fn)).get("words",[]): used.add(w["en"].lower())

pool=json.load(open(ROOT/POOLF))["words"]
selmap={w["w"]:w for w in pool}
ordered=[w["w"] for w in pool if w["w"].lower() not in used]

index=json.load(open(CORPUS/"index.json"))
exams=[]
for row in index:
    raw=subprocess.run(["pdftotext","-raw",str(TESTDIR/row["file"]),"-"],
                       capture_output=True,text=True,timeout=60).stdout
    exams.append((row["label"], split_items(raw)))

def good(s):
    if "____" in s or " / " in s: return False
    if not s or s[0].islower(): return False
    n=len(s.split()); return 7<=n<=28
def exact(s,w):
    return bool(re.search(r"\b"+re.escape(w)+r"(s|es|ed|d|ing|al|ally|ly|ity|ies)?\b",s,re.I))
def cands_for(w):
    rx=stem_re(w); by={}; yrs=set()
    for label,items in exams:
        for num,text in items.items():
            for s in sentences(text):
                if rx.search(s):
                    yrs.add(int(label.split()[0]))
                    sc=(good(s),exact(s,w),-abs(16-len(s.split())))
                    if label not in by or sc>by[label][0]:
                        by[label]=(sc,{"label":label,"item":num,"sentence":s})
    return [v[1] for v in by.values()], (str(max(yrs)) if yrs else "")

idx=0
for N in range(START,END+1):
    chunk=ordered[idx:idx+PER]; idx+=PER
    if not chunk: print(f"Day{N}: 풀 소진"); break
    cc={}; rec={}
    for w in chunk: cc[w],rec[w]=cands_for(w)
    used_ex=set()
    for w in sorted(chunk,key=lambda w:len(cc[w])):
        pool_c=cc[w]; fresh=[c for c in pool_c if c["label"] not in used_ex] or pool_c
        pk=max(fresh,key=lambda c:(good(c["sentence"]),exact(c["sentence"],w))) if fresh else None
        if pk: used_ex.add(pk["label"])
        cc[w]=("PICK",pk)
    out={"book":BOOK,"code":CODE,"day":N,"words":[]}
    for w in chunk:
        pk=cc[w][1]; sm=selmap[w]
        out["words"].append({
            "en":w,"ipa":"","pos":"",
            "meanings":[{"pos":"","ko":"","ex":"","tr":"","src":f"{pk['label']} {pk['item']}번" if pk else ""}],
            "syn":[],"deriv":[],"roots":[],"etymHint":"","level":"",
            "exam":{"tested":True,"count":sm["total"],"exams":sm["exams"],"recentYear":rec[w],"stars":sm["stars"]},
            "_ref":pk["sentence"] if pk else ""})
    json.dump(out,open(ROOT/f"suneung-{PREFIX}-day{N}.scaffold.json","w"),ensure_ascii=False,indent=1)
    print(f"Day{N}: {len(chunk)}단어 {len(used_ex)}시험 ({chunk[0]}…{chunk[-1]})")
print(f"\n남은 풀: {len(ordered)-idx}")
