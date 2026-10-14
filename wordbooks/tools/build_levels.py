#!/usr/bin/env python3
"""
중등 3권 + 수능 3권(단어책)을 하나로 합쳐 레벨 6권으로 다시 나눈다.

왜:
  기존 구분은 '레벨' 이 아니라 '학년' 이었다. 그래서 B1 이 세 권(중등 완성·수능
  기본·수능 핵심)에 흩어지고, '수능 고난도' 의 상당수가 실은 B2 였다. 게다가
  책끼리 겹치는 단어가 846개라 이어서 공부하면 그만큼을 다시 외운다.

어떻게:
  1) 여섯 권의 최종 Day JSON 을 쉬운 책부터 순서대로 읽는다
  2) en(소문자) 기준으로 중복 제거 — 먼저 나온 쪽(= 더 쉬운 책)의 설명을 남긴다
  3) (CEFR, 원래 책 순서, Day, Day 안 순서) 로 정렬 → 난이도가 매끄럽게 올라간다
  4) 권당 정해진 개수로 끊고, 권 안에서 40개씩 Day 로 나눈다

출력: suneung-lv<N>-day<D>.json  (기존 도구 glob 과 호환)
실행: python3 tools/build_levels.py          미리보기
      python3 tools/build_levels.py --go     파일 생성
"""
import json, glob, re, sys, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GO = "--go" in sys.argv

# 쉬운 책부터. 같은 CEFR 안에서는 이 순서가 2차 정렬 기준이 된다
# (원저자가 잡아둔 '기초어 먼저' 순서를 그대로 물려받는다)
SRC = ['mid1', 'mid2', 'mid3', 'basic', 'core', 'hard']
LVRANK = {'A1':0, 'A2':1, 'B1':2, 'B2':3, 'C1':4, 'C2':5}

# (prefix, 제목, 코드, 단어 수, 하루 분량)
# 하루 분량이 권마다 다르다 — 입문·기초 단계에서 하루 40개는 외우다 지친다.
# 처음 두 권만 20개로 두고, 어휘에 익숙해지는 Lv.3 부터 40개로 올린다.
BOOKS = [
    ('lv1', 'Lv.1 입문',   'IMV-L1', 800,  20),
    ('lv2', 'Lv.2 기초',   'IMV-L2', 800,  20),
    ('lv3', 'Lv.3 기본',   'IMV-L3', 800,  40),
    ('lv4', 'Lv.4 중급',   'IMV-L4', 800,  40),
    ('lv5', 'Lv.5 상급',   'IMV-L5', 800,  40),
    ('lv6', 'Lv.6 최상급', 'IMV-L6', None, 40),   # None = 나머지 전부
]

# 단어가 아니라 고유명사다. 기출 지문에서 뽑히면서 섞여 들어왔다.
# (bach=작곡가, burke/peterson/robinson=사람 이름) 재편하는 김에 뺀다.
DROP = {'bach', 'burke', 'peterson', 'robinson'}
NOTE = ('예문은 실제 기출 지문을 CEFR 수준에 맞춰 재작성한 기출변형이거나 '
        '자체 집필한 문장입니다.')

def load_all():
    rows, seen, dup = [], {}, 0
    for rank, pre in enumerate(SRC):
        files = sorted(glob.glob(str(ROOT / f'suneung-{pre}-day*.json')),
                       key=lambda p: int(re.search(r'day(\d+)', p).group(1)))
        for f in files:
            d = json.load(open(f, encoding='utf-8'))
            day = int(d['day'])
            for i, w in enumerate(d['words']):
                key = (w.get('en') or '').lower().strip()
                if not key:
                    continue
                if key in DROP:
                    continue
                if key in seen:
                    dup += 1
                    continue
                seen[key] = True
                lv = (w.get('level') or 'B1').upper()
                rows.append({'sort': (LVRANK.get(lv, 2), rank, day, i), 'w': w, 'lv': lv})
    rows.sort(key=lambda r: r['sort'])
    return rows, dup

def main():
    rows, dup = load_all()
    total = len(rows)
    # 마지막 권은 나머지 전부
    sizes = [b[3] for b in BOOKS]
    fixed = sum(s for s in sizes if s)
    sizes = [s if s else total - fixed for s in sizes]
    assert sum(sizes) == total, (sum(sizes), total)
    perday = [b[4] for b in BOOKS]

    print(f'원본 6권 합계 {total + dup:,}개 → 중복 {dup:,}개 제거 → 고유 {total:,}개\n')
    print(f"{'권':<12}{'단어':>6}{'일':>5}{'하루':>5}   레벨 구성")
    out, at, alldays = [], 0, 0
    for (pre, title, code, _, pd), size in zip(BOOKS, sizes):
        chunk = rows[at:at + size]; at += size
        c = collections.Counter(r['lv'] for r in chunk)
        comp = ' · '.join(f'{l} {c[l]}' for l in ['A1','A2','B1','B2','C1','C2'] if c[l])
        days = -(-size // pd); alldays += days
        print(f'{title:<12}{size:>6}{days:>5}일{pd:>5}개   {comp}')
        for d in range(days):
            ws = [r['w'] for r in chunk[d*pd:(d+1)*pd]]
            out.append((f'suneung-{pre}-day{d+1}.json',
                        {'book': title, 'code': code, 'day': d+1,
                         'words': ws, 'exampleNote': NOTE}))
    print(f"\n{'합계':<12}{total:>6}{alldays:>5}일")

    # 검증 — 단어 유실·중복이 없어야 한다
    allw = [w['en'].lower().strip() for _, d in out for w in d['words']]
    assert len(allw) == total, (len(allw), total)
    assert len(set(allw)) == total, '새 6권 안에 중복이 있다'
    print('검증: 유실 0 · 중복 0')

    if not GO:
        print('\n(미리보기입니다. 실제로 쓰려면 --go)')
        return
    for fn, data in out:
        (ROOT / fn).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'\n{len(out)}개 파일 생성 완료')

main()
