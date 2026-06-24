#!/usr/bin/env python3
"""
무료 맛보기 PDF용 책 조판 HTML 생성 (Day1~5, 200단어) + 표지/사용법/앱CTA.
출력: wordbooks/free-sample/imvoca-suneung-basic-sample.html
렌더: Google Chrome --headless --print-to-pdf 로 PDF화(아래 별도 명령).
"""
import json, html, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_quiz import checkup_html, QUIZ_CSS
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT/"free-sample"; OUT.mkdir(exist_ok=True)
DAYS = [1,2,3,4,5]

LV = {'C2':'#7b2d8b','C1':'#c0392b','B2':'#e67e22','B1':'#2980b9','A2':'#27ae60','A1':'#95a5a6'}
def esc(s): return html.escape(str(s or ''))

def entry_html(w):
    m = w['meanings']; m0 = m[0]
    lv = w.get('level','')
    pill = f'<span class="lv" style="background:{LV.get(lv,"#999")}">CEFR {esc(lv)}</span>' if lv else ''
    src = m0.get('src','')
    badge = f'<span class="src">🎯 {esc(src)} 기출변형</span>' if src else (
            f'<span class="src">🎯 기출 {w["exam"]["exams"]}개 시험</span>' if w.get("exam",{}).get("tested") else '')
    means = ''.join(
        f'<div class="mean"><span class="num">{["①","②","③"][i] if i<3 else "·"}</span>'
        f'<span class="pos">{esc(mm.get("pos",""))}</span> {esc(mm.get("ko",""))}</div>'
        for i,mm in enumerate(m))
    chips=[]
    if w.get('syn'): chips.append(f'<span class="chip"><b>유의어</b> {esc(" · ".join(w["syn"]))}</span>')
    if w.get('deriv'): chips.append(f'<span class="chip"><b>파생</b> {esc(" · ".join(w["deriv"]))}</span>')
    chiprow = f'<div class="chips">{"".join(chips)}</div>' if chips else ''
    etym = f'<div class="etym"><b>어원</b> {esc(w["etymHint"])}</div>' if w.get('etymHint') else ''
    exbox = ''
    if m0.get('ex'):
        exbox = (f'<div class="exbox">{badge}'
                 f'<div class="ex">{esc(m0["ex"])}</div>'
                 f'<div class="tr">{esc(m0.get("tr",""))}</div></div>')
    return (f'<div class="entry">'
            f'<div class="head"><span class="en">{esc(w["en"])}</span>'
            f'<span class="ipa">{esc(w.get("ipa",""))}</span>{pill}</div>'
            f'<div class="means">{means}</div>'
            f'{exbox}{chiprow}{etym}</div>')

def day_section(n):
    d = json.load(open(ROOT/f"suneung-basic-day{n}.json"))
    entries = ''.join(entry_html(w) for w in d['words'])
    words = (f'<section class="day"><div class="dayhead"><span class="dnum">DAY {n}</span>'
             f'<span class="dsub">수능 기본 · {len(d["words"])} words</span></div>{entries}</section>')
    return words + checkup_html(d)   # 단어 뒤에 단원 점검 페이지

body = ''.join(day_section(n) for n in DAYS)
total = sum(len(json.load(open(ROOT/f"suneung-basic-day{n}.json"))["words"]) for n in DAYS)

DOC = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>IM VOCA 수능 기본 영단어 — 맛보기</title>
<style>
:root{{--navy:#1c3553;--gold:#b8860b;--ink:#2b2b2b;--ink60:#6b7280;--line:#e7e3da;--cream:#faf7f1;}}
*{{box-sizing:border-box;}}
@page{{size:A4;margin:15mm 16mm;}}
@page full{{margin:0;}}
html,body{{margin:0;padding:0;color:var(--ink);
 font-family:'Apple SD Gothic Neo','Pretendard','Noto Sans KR',sans-serif;
 -webkit-print-color-adjust:exact;print-color-adjust:exact;font-size:10.5pt;line-height:1.5;}}
.serif{{font-family:Georgia,'Times New Roman',serif;}}

/* 표지 */
.cover{{page:full;width:210mm;height:297mm;display:flex;flex-direction:column;justify-content:center;
 align-items:center;text-align:center;page-break-after:always;background:var(--navy);color:#fff;
 padding:0 26mm;}}
.cover .badge{{font-size:12pt;letter-spacing:3px;color:#e9c46a;font-weight:700;margin-bottom:18px;}}
.cover h1{{font-size:34pt;margin:0 0 6px;font-weight:800;line-height:1.2;}}
.cover h2{{font-size:15pt;font-weight:400;color:#cdd6e0;margin:0 0 28px;}}
.cover .meta{{font-size:11pt;color:#e9c46a;border-top:1px solid rgba(255,255,255,.25);
 border-bottom:1px solid rgba(255,255,255,.25);padding:12px 0;margin-top:8px;}}
.cover .brand{{position:relative;margin-top:46px;font-size:13pt;font-weight:700;}}
.cover .free{{display:inline-block;margin-top:14px;background:#e9c46a;color:var(--navy);
 font-weight:800;border-radius:99px;padding:6px 18px;font-size:11pt;}}

/* 사용법 */
.intro{{page-break-after:always;}}
.intro h3{{font-size:17pt;color:var(--navy);border-bottom:2px solid var(--gold);
 padding-bottom:6px;margin:0 0 16px;}}
.intro p{{color:#444;margin:0 0 12px;}}
.legend{{background:var(--cream);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:14px 0;}}
.legend .row{{margin:7px 0;}}
.lvkey{{display:inline-block;color:#fff;border-radius:99px;padding:1px 8px;font-size:8.5pt;font-weight:700;margin-right:4px;}}

/* Day 섹션 */
.dayhead{{display:flex;align-items:baseline;gap:10px;border-bottom:2px solid var(--navy);
 margin:6px 0 12px;padding-bottom:5px;page-break-after:avoid;}}
.dayhead .dnum{{font-size:16pt;font-weight:800;color:var(--navy);letter-spacing:1px;}}
.dayhead .dsub{{font-size:9pt;color:var(--ink60);}}
.day{{page-break-before:always;}}

/* 단어 엔트리 */
.entry{{page-break-inside:avoid;border-bottom:1px solid var(--line);padding:9px 0 10px;}}
.head{{display:flex;align-items:baseline;gap:9px;}}
.head .en{{font-family:Georgia,serif;font-size:15pt;font-weight:700;color:var(--navy);}}
.head .ipa{{font-family:Georgia,serif;font-size:9.5pt;color:var(--ink60);}}
.lv{{margin-left:auto;color:#fff;border-radius:99px;padding:1px 9px;font-size:8pt;font-weight:700;}}
.means{{margin:3px 0 0;}}
.mean{{font-size:10.5pt;margin:1px 0;}}
.mean .num{{color:var(--gold);font-weight:700;margin-right:3px;}}
.mean .pos{{color:#9a7b3a;font-style:italic;font-size:9.5pt;margin-right:3px;}}
.exbox{{background:var(--cream);border-left:3px solid var(--gold);border-radius:4px;
 padding:6px 10px;margin:6px 0 5px;}}
.exbox .src{{display:inline-block;font-size:8pt;font-weight:700;color:#b03a2e;
 background:#fbeae7;border-radius:5px;padding:1px 7px;margin-bottom:4px;}}
.exbox .ex{{font-family:Georgia,serif;font-size:10.5pt;color:#26303d;line-height:1.45;}}
.exbox .tr{{font-size:9.5pt;color:var(--ink60);margin-top:2px;}}
.chips{{font-size:9pt;color:#555;margin:3px 0;}}
.chip{{margin-right:12px;}}
.chip b{{color:var(--navy);font-weight:700;}}
.etym{{font-size:9pt;color:#6a5a2e;background:#fcf8ee;border-radius:4px;padding:3px 8px;margin-top:3px;}}
.etym b{{color:var(--gold);}}

/* CTA */
.cta{{page:full;page-break-before:always;width:210mm;height:297mm;display:flex;flex-direction:column;
 justify-content:center;align-items:center;text-align:center;
 background:var(--navy);color:#fff;padding:0 26mm;}}
.cta h2{{font-size:24pt;font-weight:800;margin:0 0 10px;line-height:1.3;}}
.cta p{{font-size:13pt;color:#cdd6e0;margin:0 0 8px;max-width:135mm;}}
.cta .feat{{text-align:left;margin:22px 0;font-size:12pt;line-height:2;}}
.cta .feat b{{color:#e9c46a;}}
.cta .url{{margin-top:18px;font-size:18pt;font-weight:800;color:#e9c46a;letter-spacing:1px;}}
.cta .small{{font-size:9.5pt;color:#9fb0c2;margin-top:24px;}}
{QUIZ_CSS}
</style></head><body>

<div class="cover">
  <div class="badge">IM VOCA · 기출 빅데이터</div>
  <h1 class="serif">수능 기본 영단어</h1>
  <h2>맛보기 · Day 1–5</h2>
  <div class="meta">기출 빈도 분석 · CEFR 난이도 · 기출변형 예문 + 출처</div>
  <div class="free">무료 샘플 · {total} words</div>
  <div class="brand">📕 imvoca.app</div>
</div>

<div class="intro">
  <h3>이 책은 무엇이 다른가</h3>
  <p>출판사 단어장을 베끼지 않았습니다. <b>2009~2027년 수능·모의평가 기출 코퍼스</b>를 직접 분석해
  실제로 자주 나온 단어만 빈도순으로 뽑고, 뜻·예문·어원을 자체 제작했습니다.</p>
  <p>모든 예문은 <b>그 단어가 실제 출제된 기출 지문을 CEFR 수준에 맞춰 재작성한 “기출변형”</b>이며,
  <b>출처(연도·회차·문항번호)</b>를 함께 표기했습니다.</p>
  <div class="legend">
    <div class="row"><b>CEFR 난이도</b> &nbsp;
      <span class="lvkey" style="background:#2980b9">B1</span>
      <span class="lvkey" style="background:#e67e22">B2</span>
      <span class="lvkey" style="background:#c0392b">C1</span> — 유럽언어기준 난이도</div>
    <div class="row"><span class="lvkey" style="background:#b03a2e">🎯 기출변형</span>
      실제 기출 지문 기반 예문 + 출처</div>
    <div class="row"><b>① ②</b> 빈출 의미 순 · <b>유의어/파생/어원</b>으로 확장 학습</div>
  </div>
  <p style="color:#888;font-size:9pt;">※ 이 PDF는 전체 1,200단어 중 Day 1–5(200단어) 맛보기입니다.
  나머지와 원어민 발음·망각곡선 복습은 IM VOCA 앱에서 제공됩니다.</p>
</div>

{body}

<div class="cta">
  <h2>이건 시작일 뿐이에요</h2>
  <p>방금 본 200단어는 전체의 <b style="color:#e9c46a">6분의 1</b>입니다.</p>
  <div class="feat">
    📚 <b>수능 기본 1,200단어</b> 전권<br>
    🔊 <b>원어민 발음</b> 듣기 (모든 단어)<br>
    🔁 <b>망각곡선 복습</b> — 1·2·3·6·15·30일 자동 스케줄<br>
    🎯 <b>기출변형 예문 + 출처</b> · CEFR 난이도<br>
    📈 학습 진도 · 퀴즈 모드
  </div>
  <p>전부 앱에서. 지금 시작하세요.</p>
  <div class="url">imvoca.app</div>
  <div class="small">IM VOCA · 기출 빅데이터 기반 영단어 학습</div>
</div>

</body></html>"""

(OUT/"imvoca-suneung-basic-sample.html").write_text(DOC, encoding="utf-8")
print(f"HTML 생성: free-sample/imvoca-suneung-basic-sample.html ({total} words, {len(DAYS)} days)")
