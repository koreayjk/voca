#!/usr/bin/env python3
"""
스캐폴드(suneung-basic-day<N>.scaffold.json) + 콘텐츠(day<N>.content.json) → 최종 Day JSON.
콘텐츠 형식: { "<en>": {ipa,pos,level,meanings:[{pos,ko,ex,tr},...],syn[],deriv[],roots[],etymHint}, ... }
- src/exam/recentYear 는 스캐폴드 값 유지(정합성)
- 첫 meaning 에 스캐폴드의 src 주입, _ref 제거
사용: merge_day.py <N>
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
N = int(sys.argv[1])
PREFIX = sys.argv[2] if len(sys.argv) > 2 else "basic"
scaf = json.load(open(ROOT/f"suneung-{PREFIX}-day{N}.scaffold.json"))
_cf = f"day{N}.content.json" if PREFIX == "basic" else f"{PREFIX}-day{N}.content.json"
content = json.load(open(ROOT/_cf))

out = {"book":scaf["book"],"code":scaf["code"],"day":N,
       "exampleNote":"예문은 실제 기출 지문(연도·회차·문항 표기)을 CEFR 수준에 맞춰 재작성한 기출변형입니다.",
       "words":[]}
missing=[]
for sw in scaf["words"]:
    en=sw["en"]
    c=content.get(en)
    if not c: missing.append(en); continue
    src=sw["meanings"][0].get("src","")
    means=[]
    for i,m in enumerate(c["meanings"]):
        mm={"pos":m["pos"],"ko":m["ko"]}
        if i==0:
            mm["ex"]=m["ex"]; mm["tr"]=m["tr"]; mm["src"]=src
        means.append(mm)
    word={"en":en,"ipa":c["ipa"],"pos":c["pos"],"meanings":means,
          "syn":c.get("syn",[]),"deriv":c.get("deriv",[]),
          "roots":c.get("roots",[]),"etymHint":c.get("etymHint",""),
          "level":c["level"],"exam":sw["exam"]}
    out["words"].append(word)
if missing:
    print("WARNING missing content:", missing); sys.exit(1)
json.dump(out, open(ROOT/f"suneung-{PREFIX}-day{N}.json","w"), ensure_ascii=False, indent=1)
print(f"Day{N} 완성: {len(out['words'])}단어 → suneung-{PREFIX}-day{N}.json")
