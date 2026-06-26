#!/usr/bin/env python3
"""
corpus/*.txt(추출한 기출 시험 텍스트)에서 깊은 빈도 풀 생성 → suneung-pool-full.json
- total(총 등장) + exams(등장 시험수) → stars(≥20:3 · 8~19:2 · 1~7:1)
- 필터: 스톱워드(tools/stopwords.txt) · 축약형 · 복수형 · -ing/-ed · 부사(-ly) · 고유명사(대소문자 분석)
- 핵심/고난도 등 책 단어 공급용. (corpus/ 는 저작권 원문이라 gitignore → 이 스크립트는 로컬에서만 실행됨)
"""
import json, re, glob
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT/"corpus"

STOP=set()
for ln in open(ROOT/"tools"/"stopwords.txt",encoding="utf-8"):
    for t in ln.split("#")[0].split(): STOP.add(t.lower())
KEEP_S={'species','series','means','news','goods','analysis','basis','crisis','focus','status','process',
        'access','business','success','progress','address','witness','illness','awareness','emphasis',
        'consciousness','wilderness','fitness','darkness','kindness','happiness','weakness','perhaps','always',
        'towards','various','previous','serious','obvious','famous','nervous','numerous','religious','conscious',
        'gas','bias','virus','campus','bonus','thesis','hypothesis','apparatus','stimulus','consensus'}
ICS_KEEP={'economics','physics','mathematics','politics','statistics','ethics','logistics','genetics',
          'linguistics','electronics','dynamics','athletics','mechanics','optics','aesthetics','semantics'}
ADV_KEEP={'supply','apply','reply','rely','comply','imply','multiply','ally','rally','bully',
          'assembly','anomaly','monopoly','melancholy','family','only','early','italy','july','ply','fly','sly'}
def is_plural(s):
    if s in KEEP_S: return False
    if s.endswith('ics'): return s not in ICS_KEEP
    if s.endswith(('ss','us','is','ous','ness','sis')): return False
    return s.endswith('s')
def is_adverb(s):
    return s.endswith('ly') and len(s)>4 and s not in ADV_KEEP
def ok(s):
    return (len(s)>=3 and s.isalpha() and s not in STOP
            and not s.endswith('ing') and not s.endswith('ed')
            and not is_plural(s) and not is_adverb(s))

total=defaultdict(int); exams=defaultdict(int); capmid=defaultdict(int); lower=defaultdict(int)
files=sorted(CORPUS.glob("*.txt"))
for f in files:
    txt=f.read_text(encoding="utf-8",errors="ignore")
    seen=set()
    for m in re.finditer(r"[A-Za-z]{3,}", txt):
        w=m.group(0); lw=w.lower()
        total[lw]+=1; seen.add(lw)
        j=m.start()-1
        while j>=0 and txt[j] in " \t\n\r": j-=1
        sent_start = (j<0) or (txt[j] in ".!?:;\"'·•")
        if w[0].isupper() and not sent_start: capmid[lw]+=1
        elif w[0].islower(): lower[lw]+=1
    for w in seen: exams[w]+=1

def is_proper(w):
    cm=capmid[w]; lo=lower[w]
    return cm>=2 and cm >= (cm+lo)*0.55   # 문장중간 대문자 비율 높으면 고유명사
def stars(e): return 3 if e>=20 else (2 if e>=8 else 1)
pool=[{"w":w,"total":total[w],"exams":exams[w],"stars":stars(exams[w])}
      for w in total if ok(w) and not is_proper(w)]
pool.sort(key=lambda x:(-x["stars"],-x["exams"],-x["total"]))
json.dump({"corpusExams":len(files),"words":pool}, open(ROOT/"suneung-pool-full.json","w"),
          ensure_ascii=False, indent=0)
print(f"pool: {len(pool)} words → suneung-pool-full.json (corpus {len(files)} exams)")
