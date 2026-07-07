#!/usr/bin/env python3
"""
TOEIC 무료 맛보기 PDF 조판 HTML (토익 기초 Day1~5, 200단어) — 카드 뒷면 전체 정보 반영.
단어마다: 뜻·발음·비즈니스 예문·해석·유의어·파생어·빈출표현(콜로케이션)·💡시험팁.
각 Day 뒤에 CHECK-UP(단원 점검) 1페이지.
출력: wordbooks/free-sample/imvoca-toeic-basic-sample.html → Chrome headless로 PDF.
"""
import json, html, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_quiz import checkup_html, QUIZ_CSS
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT/"free-sample"; OUT.mkdir(exist_ok=True)
PREFIX = "toeic1"; BOOKNAME = "토익 기초"; SCORE = "600점대"
DAYS = [1,2,3,4,5]
def esc(s): return html.escape(str(s or ''))

def entry_html(w):
    m = w['meanings']; m0 = m[0]
    lv = w.get('level','')
    pill = f'<span class="lv">TOEIC {esc(lv)}</span>' if lv else ''
    means = ''.join(
        f'<div class="mean"><span class="num">{["①","②","③"][i] if i<3 else "·"}</span>'
        f'<span class="pos">{esc(mm.get("pos",""))}</span> {esc(mm.get("ko",""))}</div>'
        for i,mm in enumerate(m))
    exbox = ''
    if m0.get('ex'):
        exbox = (f'<div class="exbox"><span class="src">💼 비즈니스 예문</span>'
                 f'<div class="ex">{esc(m0["ex"])}</div>'
                 f'<div class="tr">{esc(m0.get("tr",""))}</div></div>')
    chips=[]
    if w.get('syn'): chips.append(f'<span class="chip"><b>유의어</b> {esc(" · ".join(w["syn"]))}</span>')
    if w.get('deriv'): chips.append(f'<span class="chip"><b>파생</b> {esc(" · ".join(w["deriv"]))}</span>')
    chiprow = f'<div class="chips">{"".join(chips)}</div>' if chips else ''
    colloc = ''
    if w.get('colloc'):
        rows = ''.join(f'<div class="clrow">· {esc(c)}</div>' for c in w['colloc'])
        colloc = f'<div class="colloc"><span class="cltag">빈출 표현</span>{rows}</div>'
    tip = f'<div class="tip">💡 {esc(w["tip"])}</div>' if w.get('tip') else ''
    return (f'<div class="entry">'
            f'<div class="head"><span class="en">{esc(w["en"])}</span>'
            f'<span class="ipa">{esc(w.get("ipa",""))}</span>{pill}</div>'
            f'<div class="means">{means}</div>{exbox}{chiprow}{colloc}{tip}</div>')

def day_section(n):
    d = json.load(open(ROOT/f"suneung-{PREFIX}-day{n}.json"))
    entries = ''.join(entry_html(w) for w in d['words'])
    words = (f'<section class="day"><div class="dayhead"><span class="dnum">DAY {n}</span>'
             f'<span class="dsub">{BOOKNAME} · {len(d["words"])} words</span></div>{entries}</section>')
    return words + checkup_html(d)

body = ''.join(day_section(n) for n in DAYS)
total = sum(len(json.load(open(ROOT/f"suneung-{PREFIX}-day{n}.json"))["words"]) for n in DAYS)

DOC = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>IM VOCA 토익 기초 — 맛보기</title>
<style>
:root{{--navy:#12324a;--gold:#c79a3b;--ink:#2b2b2b;--ink60:#6b7280;--line:#e7e3da;--cream:#f7f5ef;--green:#3a7a4e;}}
*{{box-sizing:border-box;}}
@page{{size:A4;margin:15mm 16mm;}}
@page full{{margin:0;}}
html,body{{margin:0;padding:0;color:var(--ink);
 font-family:'Apple SD Gothic Neo','Pretendard','Noto Sans KR',sans-serif;
 -webkit-print-color-adjust:exact;print-color-adjust:exact;font-size:10.5pt;line-height:1.5;}}
.serif{{font-family:Georgia,'Times New Roman',serif;}}
.cover{{page:full;width:210mm;height:297mm;display:flex;flex-direction:column;justify-content:center;
 align-items:center;text-align:center;page-break-after:always;background:var(--navy);color:#fff;padding:0 26mm;}}
.cover .badge{{font-size:12pt;letter-spacing:3px;color:#e9c46a;font-weight:700;margin-bottom:18px;}}
.cover h1{{font-size:34pt;margin:0 0 6px;font-weight:800;line-height:1.2;}}
.cover h2{{font-size:15pt;font-weight:400;color:#cdd6e0;margin:0 0 28px;}}
.cover .meta{{font-size:11pt;color:#e9c46a;border-top:1px solid rgba(255,255,255,.25);
 border-bottom:1px solid rgba(255,255,255,.25);padding:12px 0;margin-top:8px;}}
.cover .brand{{margin-top:46px;font-size:13pt;font-weight:700;}}
.cover .free{{display:inline-block;margin-top:14px;background:#e9c46a;color:var(--navy);
 font-weight:800;border-radius:99px;padding:6px 18px;font-size:11pt;}}
.intro{{page-break-after:always;}}
.intro h3{{font-size:17pt;color:var(--navy);border-bottom:2px solid var(--gold);padding-bottom:6px;margin:0 0 16px;}}
.intro p{{color:#444;margin:0 0 12px;}}
.legend{{background:var(--cream);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:14px 0;}}
.legend .row{{margin:8px 0;}}
.tagkey{{display:inline-block;color:#fff;border-radius:99px;padding:1px 9px;font-size:8.5pt;font-weight:700;margin-right:5px;}}
.dayhead{{display:flex;align-items:baseline;gap:10px;border-bottom:2px solid var(--navy);
 margin:6px 0 12px;padding-bottom:5px;page-break-after:avoid;}}
.dayhead .dnum{{font-size:16pt;font-weight:800;color:var(--navy);letter-spacing:1px;}}
.dayhead .dsub{{font-size:9pt;color:var(--ink60);}}
.day{{page-break-before:always;}}
.entry{{page-break-inside:avoid;border-bottom:1px solid var(--line);padding:9px 0 10px;}}
.head{{display:flex;align-items:baseline;gap:9px;}}
.head .en{{font-family:Georgia,serif;font-size:15pt;font-weight:700;color:var(--navy);}}
.head .ipa{{font-family:Georgia,serif;font-size:9.5pt;color:var(--ink60);}}
.lv{{margin-left:auto;color:#fff;background:var(--navy);border-radius:99px;padding:1px 9px;font-size:8pt;font-weight:700;}}
.means{{margin:3px 0 0;}}
.mean{{font-size:10.5pt;margin:1px 0;}}
.mean .num{{color:var(--gold);font-weight:700;margin-right:3px;}}
.mean .pos{{color:#9a7b3a;font-style:italic;font-size:9.5pt;margin-right:3px;}}
.exbox{{background:var(--cream);border-left:3px solid var(--gold);border-radius:4px;padding:6px 10px;margin:6px 0 5px;}}
.exbox .src{{display:inline-block;font-size:8pt;font-weight:700;color:#8a6a1f;background:#f5edd8;border-radius:5px;padding:1px 7px;margin-bottom:4px;}}
.exbox .ex{{font-family:Georgia,serif;font-size:10.5pt;color:#26303d;line-height:1.45;}}
.exbox .tr{{font-size:9.5pt;color:var(--ink60);margin-top:2px;}}
.chips{{font-size:9pt;color:#555;margin:3px 0;}}
.chip{{margin-right:12px;}} .chip b{{color:var(--navy);font-weight:700;}}
.colloc{{background:#eef5ee;border:1px solid #dcead9;border-radius:6px;padding:5px 10px;margin:4px 0;}}
.colloc .cltag{{display:inline-block;font-size:8pt;font-weight:700;color:#fff;background:var(--green);border-radius:5px;padding:1px 7px;margin-bottom:2px;}}
.colloc .clrow{{font-size:9.5pt;color:#2f4a38;line-height:1.5;}}
.tip{{font-size:9pt;color:#8a6d1f;background:#fdf7e3;border:1px solid #f2e5b8;border-radius:5px;padding:4px 9px;margin-top:4px;}}
.cta{{page:full;page-break-before:always;width:210mm;height:297mm;display:flex;flex-direction:column;
 justify-content:center;align-items:center;text-align:center;background:var(--navy);color:#fff;padding:0 26mm;}}
.cta h2{{font-size:24pt;font-weight:800;margin:0 0 10px;line-height:1.3;}}
.cta p{{font-size:13pt;color:#cdd6e0;margin:0 0 8px;max-width:135mm;}}
.cta .feat{{text-align:left;margin:22px 0;font-size:12pt;line-height:2;}}
.cta .feat b{{color:#e9c46a;}}
.cta .url{{margin-top:18px;font-size:18pt;font-weight:800;color:#e9c46a;letter-spacing:1px;}}
.cta .small{{font-size:9.5pt;color:#9fb0c2;margin-top:24px;}}
{QUIZ_CSS}
</style></head><body>

<div class="cover">
  <div class="badge">IM VOCA · TOEIC</div>
  <h1 class="serif">토익 기초 VOCA</h1>
  <h2>맛보기 · Day 1–5 · {SCORE}</h2>
  <div class="meta">40회 기출 분석 · 비즈니스 예문 · 파생어 · 빈출 표현 · 시험 팁</div>
  <div class="free">무료 샘플 · {total} words</div>
  <div class="brand">📘 imvoca.app</div>
</div>

<div class="intro">
  <h3>토익, 이렇게 외우면 다릅니다</h3>
  <p>단어만 외우면 Part 5·6에서 막힙니다. IM VOCA 토익은 <b>실전 40회분 기출 분석</b>으로 빈출 단어를
  난이도별(600·800·900)로 뽑고, 각 단어를 <b>시험에 나오는 형태 그대로</b> 담았습니다.</p>
  <div class="legend">
    <div class="row"><span class="tagkey" style="background:#12324a">뜻 + 예문</span> 실전 비즈니스 상황 예문과 해석</div>
    <div class="row"><span class="tagkey" style="background:#12324a">파생어</span> advertise / advertisement / advertiser — <b>Part 5 품사문제</b> 대비</div>
    <div class="row"><span class="tagkey" style="background:#3a7a4e">빈출 표현</span> advertising budget 같은 <b>연어(덩어리)</b>로 감각 익히기</div>
    <div class="row"><span class="tagkey" style="background:#c79a3b">💡 시험 팁</span> 출제 포인트·함정 한 줄 정리</div>
  </div>
  <p style="color:#888;font-size:9pt;">※ 이 PDF는 토익 기초 30일 중 Day 1–5(200단어) 맛보기입니다.
  전체 3권(기초·핵심·고득점 2,000+단어)과 원어민 발음·망각곡선 복습은 IM VOCA 앱에서 제공됩니다.</p>
</div>

{body}

<div class="cta">
  <h2>이건 시작일 뿐이에요</h2>
  <p>방금 본 200단어는 토익 기초의 <b style="color:#e9c46a">6분의 1</b>입니다.</p>
  <div class="feat">
    📘 <b>토익 3권</b> — 기초·핵심·고득점 2,000+단어<br>
    🧩 <b>파생어·빈출표현·시험팁</b> 전 단어 수록<br>
    🔊 <b>원어민 발음</b> 듣기 (모든 단어)<br>
    🔁 <b>망각곡선 복습</b> — 자동 스케줄<br>
    📝 <b>Day별 테스트</b> · 학습 진도 관리
  </div>
  <p>전부 앱에서. 지금 시작하세요.</p>
  <div class="url">imvoca.app</div>
  <div class="small">IM VOCA · 기출 빅데이터 기반 영단어 학습</div>
</div>

</body></html>"""

(OUT/"imvoca-toeic-basic-sample.html").write_text(DOC, encoding="utf-8")
print(f"HTML 생성: free-sample/imvoca-toeic-basic-sample.html ({total} words, {len(DAYS)} days + 각 Day 테스트)")
