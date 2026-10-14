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

# 12권 · 전부 20일 · 하루 20개.
#   권마다 길이가 같아야 학원에서 '한 권 = 한 달' 로 반을 짤 수 있다.
#   그래서 권수를 먼저 정하고 단어를 고르게 나눈다 — 4,740 / 12 = 395.
#   395 는 20 으로 나누어떨어지지 않아 각 권의 마지막 Day 만 15개가 된다.
#   (한 권을 마무리하는 날이 가벼워지는 셈이라 오히려 낫다)
#   하루 20개로 고정한 이유: 빠른 학생은 하루 2페이지를 하면 되지만,
#   40개짜리 페이지는 20개로 쪼갤 수가 없다. 작은 쪽이 언제나 더 유연하다.
N_BOOKS = 12
PER_DAY = 20

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

    # 권당 단어 수를 고르게 — 나머지는 앞 권부터 한 개씩 더 준다
    base, rem = divmod(total, N_BOOKS)
    sizes = [base + (1 if i < rem else 0) for i in range(N_BOOKS)]
    assert sum(sizes) == total

    print(f'원본 6권 합계 {total + dup:,}개 → 중복 {dup:,}개 제거 → 고유 {total:,}개\n')
    print(f"{'권':<8}{'단어':>6}{'일':>5}{'하루':>5}   레벨 구성")
    out, at, alldays = [], 0, 0
    for i, size in enumerate(sizes, 1):
        pre, title, code = f'lv{i}', f'Lv.{i}', f'IMV-L{i}'
        chunk = rows[at:at + size]; at += size
        c = collections.Counter(r['lv'] for r in chunk)
        comp = ' · '.join(f'{l} {c[l]}' for l in ['A1','A2','B1','B2','C1','C2'] if c[l])
        days = -(-size // PER_DAY); alldays += days
        print(f'{title:<8}{size:>6}{days:>5}일{PER_DAY:>5}개   {comp}')
        for d in range(days):
            ws = [r['w'] for r in chunk[d*PER_DAY:(d+1)*PER_DAY]]
            out.append((f'suneung-{pre}-day{d+1}.json',
                        {'book': title, 'code': code, 'day': d+1,
                         'words': ws, 'exampleNote': NOTE}))
    print(f"\n{'합계':<8}{total:>6}{alldays:>5}일")

    # 검증 — 단어 유실·중복이 없어야 한다
    allw = [w['en'].lower().strip() for _, d in out for w in d['words']]
    assert len(allw) == total, (len(allw), total)
    assert len(set(allw)) == total, '새 책들 안에 중복이 있다'
    print('검증: 유실 0 · 중복 0')

    if not GO:
        print('\n(미리보기입니다. 실제로 쓰려면 --go)')
        return
    for fn, data in out:
        (ROOT / fn).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'\n{len(out)}개 파일 생성 완료')

main()
