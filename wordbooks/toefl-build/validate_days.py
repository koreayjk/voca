#!/usr/bin/env python3
# 사용법: python3 validate_days.py <prefix> <start> <end>
# 완성된 Day JSON들을 검증(40단어·중복0·필드완비·예문에 표제어 포함·큰따옴표 없음)
import json, sys, os, glob, collections

WB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prefix = sys.argv[1]
start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
end = int(sys.argv[3]) if len(sys.argv) > 3 else 999

REQ = ['en', 'ipa', 'pos', 'meanings', 'syn', 'deriv', 'level']
all_ens = []
problems = []
ok_days = []
missing = []
for d in range(start, end + 1):
    path = os.path.join(WB, f'suneung-{prefix}-day{d}.json')
    if not os.path.exists(path):
        missing.append(d)
        continue
    try:
        data = json.load(open(path))
    except Exception as e:
        problems.append((d, f'JSON파싱실패: {e}')); continue
    words = data.get('words', [])
    if len(words) != 40:
        problems.append((d, f'단어수 {len(words)}≠40'))
    ens = [w.get('en', '').lower() for w in words]
    all_ens += ens
    if len(ens) != len(set(ens)):
        problems.append((d, '파일내 중복'))
    for w in words:
        for f in REQ:
            if f not in w or w.get(f) in (None, '', []):
                if f in ('syn', 'deriv'):
                    continue
                problems.append((d, f"{w.get('en','?')}: {f} 누락")); break
        # 예문 검증
        for m in w.get('meanings', []):
            ex = m.get('ex', '')
            tr = m.get('tr', '')
            if '"' in ex or '"' in tr:
                problems.append((d, f"{w.get('en','?')}: 큰따옴표"))
            base = w.get('en', '')[:4].lower()
            if base and base not in ex.lower():
                problems.append((d, f"{w.get('en','?')}: 예문에 표제어 없음"))
            if not tr:
                problems.append((d, f"{w.get('en','?')}: 해석(tr) 없음"))
    if not any(p[0] == d for p in problems):
        ok_days.append(d)

# 책 전체 중복
dup = [e for e, c in collections.Counter(all_ens).items() if c > 1]
print(f"[{prefix}] 검사 {start}~{end}")
print(f"  완료 Day: {len(ok_days)} {ok_days if len(ok_days)<40 else ''}")
if missing:
    print(f"  미완성 Day: {missing}")
if dup:
    print(f"  ⚠️ 책내 중복 {len(dup)}: {dup[:15]}")
if problems:
    print(f"  ⚠️ 문제 {len(problems)}건:")
    for d, msg in problems[:40]:
        print(f"    Day{d}: {msg}")
else:
    print("  ✅ 문제 없음")
