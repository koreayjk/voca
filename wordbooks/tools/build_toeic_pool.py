#!/usr/bin/env python3
"""
TOEIC OCR 코퍼스(toeic-corpus/*.txt) → 빈도 풀 toeic-pool-full.json
- total(총 등장) + exams(등장 회차수) → stars
- OCR 노이즈 제거: 영어 사전(/usr/share/dict/words) 대조 + 최소 회차수 + 고유명사 감지
- 기능어/기초어는 stopwords.txt 로 일부 제외(단 TOEIC 기초는 흔한 비즈니스어 유지 위해 약하게)
- corpus/ 는 저작권(모의고사 원문)이라 gitignore → 로컬 전용
사용: build_toeic_pool.py
"""
import json, re, glob
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "toeic-corpus"

# 영어 사전(있으면 노이즈 강력 제거)
DICT = set()
for p in ("/usr/share/dict/words", "/usr/share/dict/web2"):
    try:
        for ln in open(p, encoding="utf-8", errors="ignore"):
            w = ln.strip().lower()
            if w.isalpha(): DICT.add(w)
    except FileNotFoundError:
        pass

# TOEIC은 기초 흔한 어휘도 필요 → stopwords 는 순수 기능어/축약만 최소 적용
STOP = set("""a an the and or but if of to in on at by for with from as is are was were be been being
am do does did have has had will would can could shall should may might must not no nor so than then
this that these those it its it's i you he she we they them him her his hers our your their my me us
what which who whom whose when where why how all any both each few more most other some such only own
same very s t don just now here there out up down off over under again once about into through during
i'm you're he's she's we're they're i've i'll don't can't won't isn't aren't wasn't didn't doesn't""".split())

# TOEIC 문제 형식·지시문 단어(가르칠 어휘 아님) 제외 — 순수 mechanical 만(문서종류어 email/report 등은 유지)
TOEIC_BOILER = set("""question questions refer refers following directions passage speaker speakers likely
indicate indicated indicates suggest suggested suggests imply implied implies mention mentioned mentions
according choose select mark sheet complete completes blank blanks excerpt narrator probably purpose
paragraph true false option options nearest meaning phrase closest part test man woman men women answer
answers see please take make need get know look use say let well sure right one like new next""".split())
STOP |= TOEIC_BOILER
STOP |= set("ole tot els ona com oe ooe eal tol ol ee oo  ce ical ing tion ally".split())  # 잦은 OCR 오탈자
# 수능 stopwords(기능어·기초어) 도 제외 → TOEIC 기초가 실제 비즈니스 어휘부터 시작
try:
    for ln in open(ROOT / "tools" / "stopwords.txt", encoding="utf-8"):
        for tkn in ln.split("#")[0].split(): STOP.add(tkn.lower())
except FileNotFoundError:
    pass

def is_proper(w, capmid, lower):
    cm, lo = capmid[w], lower[w]
    return cm >= 3 and cm >= (cm + lo) * 0.6

def ok(w):
    if len(w) < 3 or not w.isalpha(): return False
    if w in STOP: return False
    return True

total = defaultdict(int); exams = defaultdict(int)
capmid = defaultdict(int); lower = defaultdict(int)
files = sorted(CORPUS.glob("*.txt"))
if not files:
    print("toeic-corpus/*.txt 없음 — 먼저 OCR 완료 필요"); raise SystemExit(1)

for f in files:
    txt = f.read_text(encoding="utf-8", errors="ignore")
    seen = set()
    for m in re.finditer(r"[A-Za-z]{2,}", txt):
        w = m.group(0); lw = w.lower()
        total[lw] += 1; seen.add(lw)
        j = m.start() - 1
        while j >= 0 and txt[j] in " \t\r": j -= 1
        sent_start = (j < 0) or (txt[j] in ".!?:;\"'\n")
        if w[0].isupper() and not sent_start: capmid[lw] += 1
        elif w[0].islower(): lower[lw] += 1
    for w in seen: exams[w] += 1

def stars(e): return 3 if e >= 25 else (2 if e >= 10 else 1)

pool = []
for w in total:
    if not ok(w): continue
    # 노이즈 필터: 사전에 반드시 존재해야 함(OCR 오탈자 ona/tol/eal 제거). 사전 없을 때만 회차 fallback.
    if DICT:
        if w not in DICT: continue
    elif exams[w] < 4: continue
    if is_proper(w, capmid, lower): continue
    if exams[w] < 3: continue   # 최소 3회차 등장 (OCR 노이즈·단발어 제거)
    pool.append({"w": w, "total": total[w], "exams": exams[w], "stars": stars(exams[w])})

pool.sort(key=lambda x: (-x["exams"], -x["total"]))
json.dump({"corpusExams": len(files), "words": pool},
          open(ROOT / "toeic-pool-full.json", "w"), ensure_ascii=False, indent=0)
print(f"TOEIC pool: {len(pool)} words (회차 {len(files)}, 사전 {len(DICT)}) → toeic-pool-full.json")
print("상위 30:", [p["w"] for p in pool[:30]])
