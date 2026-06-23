#!/usr/bin/env python3
"""
Day3..DayMAX 스캐폴드를 한 번에 생성(결정적 단어선정).
- day1/day2 사용단어 제외, 선택풀을 (stars,exams,total)순 정렬 + 기능어/기초어 스톱
- 40단어씩 청크 → 각 Day
- 코퍼스는 1회 로드, 각 Day마다 회차 골고루 출처배정 + recentYear
사용: build_all_scaffolds.py <START> <END>   예) 3 30
"""
import json, sys, re, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
TESTDIR=(ROOT/".."/".."/"test").resolve()
CORPUS=ROOT/"corpus"
sys.path.insert(0,str(ROOT/"tools"))
from find_occurrences import stem_re, split_items, sentences

START,END=int(sys.argv[1]),int(sys.argv[2])
PER=40

# 사용단어
used=set()
for f in sorted(ROOT.glob("suneung-basic-day*.json")):
    if ".scaffold." in f.name: continue
    for w in json.load(open(f)).get("words",[]): used.add(w["en"].lower())

# 스톱
STOP=set()
for ln in (ROOT/"tools"/"stopwords.txt").read_text(encoding="utf-8").splitlines():
    for t in ln.split("#")[0].split(): STOP.add(t.lower())
KEEP_S={"species","series","means","news","goods","analysis","basis","crisis","focus",
        "status","process","access","business","success","progress","address","witness",
        "illness","awareness","emphasis","consciousness","wilderness","fitness","darkness",
        "kindness","happiness","weakness","perhaps","always","towards","various","previous",
        "serious","obvious","famous","nervous","numerous","religious","conscious","gas","bias","virus","campus","bonus","crisis","thesis"}
def is_plural(s):
    sl=s.lower()
    if sl in KEEP_S: return False
    if sl.endswith("ics"): return False     # economics, physics, politics
    if sl.endswith(("ss","us","is","ous","ness","sis")): return False
    return sl.endswith("s")
def ok(s):
    sl=s.lower()
    return (s.isalpha() and len(s)>=3 and sl not in STOP
            and not s.endswith("ing") and not s.endswith("ed")
            and not is_plural(s))

sel=json.load(open(ROOT/"suneung-selection.json"))["words"]
selmap={w["w"]:w for w in sel}
ordered=[w["w"] for w in sorted(sel,key=lambda w:(-w["stars"],-w["exams"],-w["total"]))
         if w["w"].lower() not in used and ok(w["w"])]

# 코퍼스 로드
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
    used_ex=set(); rows=[]
    # 후보 계산
    cc={}; rec={}
    for w in chunk:
        cc[w],rec[w]=cands_for(w)
    for w in sorted(chunk,key=lambda w:len(cc[w])):
        pool=cc[w]; fresh=[c for c in pool if c["label"] not in used_ex] or pool
        if fresh:
            pk=max(fresh,key=lambda c:(good(c["sentence"]),exact(c["sentence"],w)))
            used_ex.add(pk["label"])
        else: pk=None
        cc[w]=("PICK",pk)
    out={"book":"수능 기본","code":"SUN-BASIC","day":N,"words":[]}
    for w in chunk:
        pk=cc[w][1]; sm=selmap[w]
        out["words"].append({
            "en":w,"ipa":"","pos":"",
            "meanings":[{"pos":"","ko":"","ex":"","tr":"","src":f"{pk['label']} {pk['item']}번" if pk else ""}],
            "syn":[],"deriv":[],"roots":[],"etymHint":"","level":"",
            "exam":{"tested":True,"count":sm["total"],"exams":sm["exams"],"recentYear":rec[w],"stars":sm["stars"]},
            "_ref":pk["sentence"] if pk else ""})
    json.dump(out,open(ROOT/f"suneung-basic-day{N}.scaffold.json","w"),ensure_ascii=False,indent=1)
    print(f"Day{N}: {len(chunk)}단어, {len(used_ex)}시험  ({chunk[0]}…{chunk[-1]})")
print(f"\n남은 풀: {len(ordered)-idx}단어")
