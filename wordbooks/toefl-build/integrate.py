#!/usr/bin/env python3
# 6개 영역 풀 통합 -> 중복제거 -> 레벨별 3권 배분 -> 주제 라운드로빈 Day 할당
import json, glob, os, collections

BUILD = os.path.dirname(os.path.abspath(__file__))
WB = os.path.dirname(BUILD)

# 1) 모든 풀 로드 + 병합
pools = {}
for f in sorted(glob.glob(os.path.join(BUILD, 'pool*.json'))):
    for w in json.load(open(f)):
        en = w['en'].strip().lower()
        if not en or ' ' in en or '-' in en:
            continue
        # 전역 중복 제거: 첫 등장 우선(학술일반=poolA 먼저 로드되어 우선순위 높음)
        if en not in pools:
            w['en'] = en
            pools[en] = w

# 2) 이미 만든 토플 Day1(40단어)은 제외(이미 toefl1 day1에 배치됨)
day1 = json.load(open(os.path.join(WB, 'suneung-toefl1-day1.json')))
day1_ens = [x['en'].lower() for x in day1['words']]
for e in day1_ens:
    pools.pop(e, None)

words = list(pools.values())
by_level = collections.defaultdict(list)
for w in words:
    by_level[w['level']].append(w)
print("중복제거 후 후보:", len(words),
      "| B2:", len(by_level['B2']), "C1:", len(by_level['C1']), "C2:", len(by_level['C2']))

# 주제 다양성 우선순위: 학술일반을 기본책에 우선 배치
def topic_key(w):
    return (0 if w['topic'] == '학술일반' else 1, w['en'])

for lv in by_level:
    by_level[lv].sort(key=topic_key)

B2, C1, C2 = by_level['B2'], by_level['C1'], by_level['C2']

# 3) 책별 배분 (정확히 기본1,200[+40기존=신규1,160] / 핵심2,000 / 고난도1,800)
#   기본  toefl1: B2 1,160 (학술일반 우선)
#   고난도 toefl3: C2 전부 + 부족분은 어려운 C1
#   핵심  toefl2: 남은 B2 + 남은 C1 -> 2,000
def take(lst, n):
    return lst[:n], lst[n:]

# 기본: B2 1,160
basic_new, B2 = take(B2, 1160)

# 고난도: C2 우선 채우고 1,800까지 C1로 보충
hard, C2 = take(C2, 1800)
if len(hard) < 1800:
    fill, C1 = take(C1, 1800 - len(hard))
    hard += fill

# 핵심: 남은 B2 + 남은 C1 -> 2,000 (부족하면 남은 C2로 보충)
core = B2 + C1
if len(core) < 2000:
    fill, C2 = take(C2, 2000 - len(core))
    core += fill
core = core[:2000]

print(f"배분 → 기본(신규):{len(basic_new)}(+40) 핵심:{len(core)} 고난도:{len(hard)}")

# 4) 주제 라운드로빈으로 Day 배열 (40단어/일)
def round_robin_by_topic(items):
    buckets = collections.OrderedDict()
    for w in items:
        buckets.setdefault(w['topic'], []).append(w)
    order = []
    while any(buckets.values()):
        for t in list(buckets.keys()):
            if buckets[t]:
                order.append(buckets[t].pop(0))
    return order

def to_days(items, start_day=1):
    ordered = round_robin_by_topic(items)
    days = {}
    for i, w in enumerate(ordered):
        d = start_day + i // 40
        days.setdefault(d, []).append(w)
    return days

# 기본: day1 고정 + 신규 day2~
basic_days = {1: [{'en': e} for e in day1_ens]}  # placeholder, 실제 콘텐츠는 기존 파일
nb = to_days(basic_new, start_day=2)
basic_days.update(nb)

core_days = to_days(core, start_day=1)
hard_days = to_days(hard, start_day=1)

# 5) 저장 (스캐폴드용 최소 정보: en,pos,ko,level,topic)
def save(prefix, days, title, code):
    out = {'book': title, 'code': code, 'prefix': prefix, 'days': {}}
    for d in sorted(days):
        out['days'][str(d)] = [
            {k: w.get(k, '') for k in ('en', 'pos', 'ko', 'level', 'topic')}
            for w in days[d]
        ]
    total = sum(len(v) for v in days.values())
    out['total'] = total
    out['num_days'] = len(days)
    path = os.path.join(BUILD, f'{prefix}-plan.json')
    json.dump(out, open(path, 'w'), ensure_ascii=False, indent=1)
    print(f"  {title}: {total}단어 / {len(days)}일 -> {os.path.basename(path)}")
    return out

print("저장:")
p1 = save('toefl1', basic_days, '토플 기본', 'TOEFL-1')
p2 = save('toefl2', core_days, '토플 핵심', 'TOEFL-2')
p3 = save('toefl3', hard_days, '토플 고난도', 'TOEFL-3')

# 6) 전역 중복 최종 검증(3권 간)
allw = []
for p in (p1, p2, p3):
    for d in p['days'].values():
        allw += [x['en'] for x in d]
dup = [e for e, c in collections.Counter(allw).items() if c > 1]
print(f"\n총 {len(allw)}단어 · 3권 간 중복: {len(dup)}")
if dup:
    print("중복샘플:", dup[:20])
