#!/usr/bin/env python3
"""
Lv.1~12 책 표지(SVG) 생성.

왜 SVG 인가: 이미지 변환 도구 없이 저장소에서 바로 만들 수 있고, 용량이
한 장에 1KB 남짓이라 12장을 다 합쳐도 사진 한 장보다 가볍다. <img> 로
그대로 렌더되므로 앱 쪽 코드는 경로만 바꾸면 된다.

실행: python3 tools/make_level_covers.py
출력: 저장소 루트의 cover-lv1.svg … cover-lv12.svg
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# (단계, CEFR, 바탕 두 색) — 입문에서 최상급으로 갈수록 어둡고 깊어진다
TIERS = {
    1:  ('입문',   'A1',      '#5b9e8f', '#3d7a6e'),
    2:  ('입문',   'A1~A2',   '#4f9392', '#356f73'),
    3:  ('입문',   'A2',      '#48879a', '#2f647b'),
    4:  ('기본',   'B1',      '#447aa0', '#2b5878'),
    5:  ('기본',   'B1',      '#426ea4', '#294d7a'),
    6:  ('기본',   'B1',      '#4162a6', '#28427b'),
    7:  ('중급',   'B1~B2',   '#45589f', '#2b3b76'),
    8:  ('중급',   'B2',      '#4b4f97', '#30346e'),
    9:  ('중급',   'B2',      '#51478c', '#352c64'),
    10: ('상급',   'B2~C1',   '#583f80', '#3a2659'),
    11: ('상급',   'C1',      '#5d3870', '#3d204d'),
    12: ('최상급', 'C1~C2',   '#5f3160', '#3b1a40'),
}

TPL = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 430" width="300" height="430">
<defs>
  <linearGradient id="g" x1="0" y1="0" x2="0.35" y2="1">
    <stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/>
  </linearGradient>
  <linearGradient id="s" x1="0" y1="0" x2="0.7" y2="1">
    <stop offset="0" stop-color="#ffffff" stop-opacity="0.22"/>
    <stop offset="0.42" stop-color="#ffffff" stop-opacity="0.05"/>
    <stop offset="0.6" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
</defs>
<rect width="300" height="430" fill="url(#g)"/>
<rect width="300" height="430" fill="url(#s)"/>
<!-- 책등 -->
<rect x="0" y="0" width="7" height="430" fill="#000" opacity="0.17"/>
<rect x="7" y="0" width="2" height="430" fill="#fff" opacity="0.10"/>

<text x="30" y="46" fill="#fff" fill-opacity="0.72" font-family="Georgia,serif"
      font-size="13" letter-spacing="3.4">IM VOCA</text>
<rect x="30" y="58" width="26" height="2" fill="#fff" opacity="0.5"/>

<text x="30" y="214" fill="#fff" font-family="Georgia,serif" font-size="{fs}"
      font-weight="bold" letter-spacing="-2">Lv.{n}</text>

<text x="31" y="256" fill="#fff" fill-opacity="0.95" font-family="'Apple SD Gothic Neo',sans-serif"
      font-size="25" font-weight="bold" letter-spacing="5">{tier}</text>

<rect x="30" y="286" width="{bw}" height="25" rx="12.5" fill="#fff" fill-opacity="0.17"/>
<text x="{bx}" y="303" fill="#fff" fill-opacity="0.92" font-family="Georgia,serif"
      font-size="13" letter-spacing="1.4">{cefr}</text>

<text x="30" y="398" fill="#fff" fill-opacity="0.6" font-family="'Apple SD Gothic Neo',sans-serif"
      font-size="12.5" letter-spacing="0.4">400단어 · 20일</text>
</svg>
'''

def main():
    for n, (tier, cefr, c1, c2) in TIERS.items():
        bw = 20 + len(cefr) * 8.2
        svg = TPL.format(n=n, tier=tier, cefr=cefr, c1=c1, c2=c2,
                         fs=74 if n < 10 else 64,
                         bw=round(bw, 1), bx=round(30 + bw / 2 - len(cefr) * 4.1, 1))
        (ROOT / f'cover-lv{n}.svg').write_text(svg, encoding='utf-8')
    print(f'{len(TIERS)}장 생성 — {ROOT}/cover-lv1.svg …')

main()
