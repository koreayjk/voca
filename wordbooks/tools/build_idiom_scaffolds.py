#!/usr/bin/env python3
"""
숙어책 스캐폴드 빌더. suneung-idiom-pool.json([{idiom,ko,pos}]) 을 받아
각 숙어를 코퍼스 독해영역에서 구(句) 단위로 매칭 → 기출 출처·예문(_ref) 배정(되는 것만).
40개씩 Day 청크 → suneung-idiom-day<N>.scaffold.json.
(corpus/ 필요 → 로컬 전용. one's/sb/sth 는 와일드카드로 매칭, 동사 굴절 일부 허용.)
사용: build_idiom_scaffolds.py
"""
import json, re, subprocess, glob
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
TESTDIR=(ROOT/".."/".."/"test").resolve()
CORPUS=ROOT/"corpus"
import sys; sys.path.insert(0,str(ROOT/"tools"))
from find_occurrences import split_items, sentences
PER=40

pool=json.load(open(ROOT/"suneung-idiom-pool.json"))["idioms"]

def idiom_rx(idiom):
    s=idiom.lower().strip()
    s=re.sub(r"\b(one's|someone's|somebody's)\b","P_POSS",s)
    s=re.sub(r"\b(somebody|someone|something|sb|sth|one)\b","P_ANY",s)
    toks=s.split()
    out=[]
    for i,w in enumerate(toks):
        if w=="p_poss": out.append(r"(?:my|your|his|her|its|our|their|\w+'s)")
        elif w=="p_any": out.append(r"\w+")
        elif i==0: out.append(re.escape(w)+r"(?:s|es|ed|ing|d)?")  # 첫 동사 굴절 일부 허용
        else: out.append(re.escape(w))
    return re.compile(r"\b"+r"\s+".join(out), re.I)

# 코퍼스 문항분리
index=json.load(open(CORPUS/"index.json"))
exams=[]
for row in index:
    raw=subprocess.run(["pdftotext","-raw",str(TESTDIR/row["file"]),"-"],
                       capture_output=True,text=True,timeout=60).stdout
    exams.append((row["label"], split_items(raw)))

def good(s):
    if "____" in s: return False
    n=len(s.split()); return 6<=n<=30

def match_idiom(idiom):
    rx=idiom_rx(idiom); by={}; yrs=set()
    for label,items in exams:
        for num,text in items.items():
            for s in sentences(text):
                if rx.search(s):
                    yrs.add(int(label.split()[0]))
                    sc=(good(s), -abs(15-len(s.split())))
                    if label not in by or sc>by[label][0]:
                        by[label]=(sc,{"label":label,"item":num,"sentence":s})
    cands=[v[1] for v in by.values()]
    return cands, (str(max(yrs)) if yrs else ""), len(by)

# 회차 골고루 배정 + Day 청크
N=1; idx=0; nmatch=0
day=[]; daynum=1; used_ex=set()
total_days = (len(pool)+PER-1)//PER
for i,it in enumerate(pool):
    cands,recent,exN = match_idiom(it["idiom"])
    fresh=[c for c in cands if c["label"] not in used_ex] or cands
    pk=max(fresh,key=lambda c:(good(c["sentence"]),)) if fresh else None
    if pk: used_ex.add(pk["label"]); nmatch+=1
    stars = 3 if exN>=20 else (2 if exN>=8 else 1) if exN else 0
    day.append({
        "en":it["idiom"],"ipa":"","pos":it.get("pos","idiom"),
        "meanings":[{"pos":it.get("pos","idiom"),"ko":it.get("ko",""),"ex":"","tr":"",
                     "src":f"{pk['label']} {pk['item']}번" if pk else ""}],
        "syn":[],"deriv":[],"roots":[],"etymHint":"","level":"",
        "exam":{"tested":bool(exN),"count":exN,"exams":exN,"recentYear":recent,"stars":stars},
        "_ref":pk["sentence"] if pk else "", "_ko":it.get("ko","")})
    if len(day)==PER or i==len(pool)-1:
        out={"book":"수능 숙어","code":"SUN-IDIOM","day":daynum,"words":day}
        json.dump(out,open(ROOT/f"suneung-idiom-day{daynum}.scaffold.json","w"),ensure_ascii=False,indent=1)
        print(f"Day{daynum}: {len(day)}개")
        day=[]; daynum+=1; used_ex=set()
print(f"\n총 {len(pool)}개 숙어 · 코퍼스 매칭(출처있음) {nmatch}개 · {daynum-1}일")
