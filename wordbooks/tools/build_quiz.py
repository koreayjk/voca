#!/usr/bin/env python3
"""
Day별 CHECK-UP(단원 점검) 문제 자동 생성.
구성: ① 뜻 연결(영→한) 10 · ② 빈칸 완성(기출변형 예문) 8 · ③ 우리말→영어 쓰기 6 = 24문항/Day.
데이터(suneung-basic-day<N>.json)만으로 생성, 정답 포함.
checkup_html(day_dict) → HTML 문자열(점검 페이지 1장). QUIZ_CSS → 스타일.
단독 실행: build_quiz.py <N> → free-sample/checkup-day<N>.html 미리보기.
"""
import json, re, html
from pathlib import Path

CIRCLED = "㉠㉡㉢㉣㉤㉥㉦㉧㉨㉩㉪㉫㉬㉭"
def esc(s): return html.escape(str(s or ''))
def ko0(w): return w['meanings'][0]['ko']

def _blank(ex, word):
    """예문에서 표제어(굴절형 포함)를 '첫글자+밑줄'로 치환. (치환형, 정답표기) 반환."""
    stem = word[:max(3, len(word)-3)]
    m = re.search(r'\b' + re.escape(stem) + r'[A-Za-z]*', ex)
    if not m:
        m = re.search(r'\b' + re.escape(word) + r'\b', ex, re.I)
    if not m:
        return ex, word
    surface = m.group(0)
    blanked = surface[0] + '_' * (len(surface) - 1)
    return ex[:m.start()] + blanked + ex[m.end():], surface

def checkup_html(day):
    ws = day['words']
    n = day['day']
    match = ws[0:10]
    blanks = ws[10:18]
    writes = ws[18:24]

    # ① 매칭: 한글 보기를 결정적으로 섞기(한글 문자열 정렬 순)
    ko_items = [(i, ko0(w)) for i, w in enumerate(match)]
    scrambled = sorted(ko_items, key=lambda t: t[1])        # 섞인 보기 순서
    pos_of = {orig_i: pos for pos, (orig_i, _) in enumerate(scrambled)}  # 원래i→보기위치
    left = ''.join(
        f'<div class="qm"><span class="qn">{i+1}.</span> '
        f'<span class="qen">{esc(w["en"])}</span> <span class="qp">(&nbsp;&nbsp;&nbsp;)</span></div>'
        for i, w in enumerate(match))
    right = ''.join(
        f'<div class="qm"><span class="qc">{CIRCLED[pos]}</span> {esc(ko)}</div>'
        for pos, (orig_i, ko) in enumerate(scrambled))
    match_ans = '  '.join(f'{i+1}-{CIRCLED[pos_of[i]]}' for i in range(len(match)))

    # ② 빈칸 완성
    blank_rows = []; blank_ans = []
    for j, w in enumerate(blanks, start=1):
        ex = w['meanings'][0].get('ex', '')
        tr = w['meanings'][0].get('tr', '')
        bex, ans = _blank(ex, w['en'])
        blank_rows.append(
            f'<div class="qb"><span class="qn">{j}.</span> {esc(bex)}'
            f'<div class="qtr">{esc(tr)}</div></div>')
        blank_ans.append(f'{j}.{ans}')
    blanks_html = ''.join(blank_rows)

    # ③ 우리말→영어 쓰기
    write_rows = []; write_ans = []
    for k, w in enumerate(writes, start=1):
        m0 = w['meanings'][0]
        write_rows.append(
            f'<div class="qw"><span class="qn">{k}.</span> '
            f'<span class="qko">{esc(m0.get("ko",""))}</span> '
            f'<span class="qline">→ ____________________</span></div>')
        write_ans.append(f'{k}.{w["en"]}')
    writes_html = ''.join(write_rows)

    answers = (f'<b>①</b> {esc(match_ans)} &nbsp;｜&nbsp; '
               f'<b>②</b> {esc(" ".join(blank_ans))} &nbsp;｜&nbsp; '
               f'<b>③</b> {esc(" ".join(write_ans))}')

    return f"""<section class="checkup">
  <div class="cuhead"><span class="cutag">CHECK-UP</span>
    <span class="cutitle">DAY {n} · 단원 점검</span>
    <span class="cusub">맞은 개수 ___ / 24</span></div>

  <div class="cusec">① 뜻을 알맞게 연결하세요 <span class="cusecn">(영→한)</span></div>
  <div class="matchgrid"><div class="mcol">{left}</div><div class="mcol">{right}</div></div>

  <div class="cusec">② 기출변형 예문의 빈칸을 채우세요 <span class="cusecn">(첫 글자 힌트)</span></div>
  <div class="blanks">{blanks_html}</div>

  <div class="cusec">③ 우리말을 보고 영어로 쓰세요</div>
  <div class="writes">{writes_html}</div>

  <div class="answers"><b>정답</b> &nbsp; {answers}</div>
</section>"""

QUIZ_CSS = """
.checkup{page-break-before:always;}
.cuhead{display:flex;align-items:baseline;gap:9px;border-bottom:2px solid var(--gold);
 margin:4px 0 12px;padding-bottom:5px;page-break-after:avoid;}
.cuhead .cutag{background:var(--gold);color:#fff;font-weight:800;font-size:8.5pt;
 border-radius:5px;padding:2px 8px;letter-spacing:1px;}
.cuhead .cutitle{font-size:14pt;font-weight:800;color:var(--navy);}
.cuhead .cusub{margin-left:auto;font-size:9.5pt;color:var(--ink60);}
.cusec{font-size:10.5pt;font-weight:700;color:var(--navy);margin:12px 0 7px;
 background:var(--cream);border-radius:5px;padding:4px 9px;page-break-after:avoid;}
.cusec .cusecn{font-weight:400;color:var(--ink60);font-size:9pt;}
.matchgrid{display:flex;gap:18px;}
.matchgrid .mcol{flex:1;}
.qm{font-size:10pt;margin:3px 0;}
.qm .qn{color:var(--gold);font-weight:700;margin-right:3px;}
.qm .qen{font-family:Georgia,serif;font-weight:700;color:#26303d;}
.qm .qp{color:var(--ink60);}
.qm .qc{color:var(--navy);font-weight:700;margin-right:4px;}
.qb{font-size:10pt;margin:7px 0;line-height:1.5;}
.qb .qn{color:var(--gold);font-weight:700;margin-right:3px;}
.qb{font-family:Georgia,serif;}
.qb .qtr{font-family:'Apple SD Gothic Neo',sans-serif;font-size:9pt;color:var(--ink60);margin-top:1px;}
.writes{display:flex;flex-wrap:wrap;}
.qw{font-size:10pt;margin:6px 0;width:50%;}
.qw .qn{color:var(--gold);font-weight:700;margin-right:3px;}
.qw .qko{color:#26303d;}
.qw .qline{color:#aaa;font-family:Georgia,serif;}
.answers{margin-top:16px;background:#f3f1ec;border:1px dashed #cfc8b8;border-radius:6px;
 padding:7px 10px;font-size:7.5pt;color:#8a8475;line-height:1.6;
 font-family:Georgia,serif;page-break-inside:avoid;}
.answers b{color:#6a6452;}
"""

if __name__ == "__main__":
    import sys
    ROOT = Path(__file__).resolve().parent.parent
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    day = json.load(open(ROOT/f"suneung-basic-day{n}.json"))
    OUT = ROOT/"free-sample"; OUT.mkdir(exist_ok=True)
    doc = (f"<!doctype html><html lang=ko><head><meta charset=utf-8><style>"
           f":root{{--navy:#1c3553;--gold:#b8860b;--ink60:#6b7280;--cream:#faf7f1;}}"
           f"body{{font-family:'Apple SD Gothic Neo',sans-serif;margin:24px;}}{QUIZ_CSS}"
           f".checkup{{page-break-before:auto;}}</style></head><body>{checkup_html(day)}</body></html>")
    (OUT/f"checkup-day{n}.html").write_text(doc, encoding="utf-8")
    print(f"checkup-day{n}.html 생성 · 정답 포함")
