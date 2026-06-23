#!/usr/bin/env python3
"""
기출 PDF(../../../test/*.pdf) → 텍스트 캐시 + 시험 라벨 인덱스.
각 PDF 헤더에서 연도/회차(수능·6월·9월 모평)를 식별해 "2025 수능" 형식 라벨을 부여한다.
출력:
  corpus/<label>.txt        (-layout 추출 텍스트, 중복 라벨이면 첫 파일만)
  corpus/index.json         [{label, year, round, file}]
재사용: 문항단위 파서 1단계.
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # wordbooks/
TESTDIR = (ROOT / ".." / ".." / "test").resolve()       # repo/../test
OUT = ROOT / "corpus"
OUT.mkdir(exist_ok=True)

def label_of(text):
    head = text[:1500]
    ym = re.search(r"(20\d{2})\s*학년도", head)
    year = ym.group(1) if ym else None
    if "6월" in head or "6 월" in head:
        rnd = "6월모평"
    elif "9월" in head or "9 월" in head:
        rnd = "9월모평"
    elif "대학수학능력시험" in head:
        rnd = "수능"
    else:
        rnd = None
    return year, rnd

def main():
    pdfs = sorted(TESTDIR.glob("*.pdf"))
    print(f"PDF {len(pdfs)}개 from {TESTDIR}", file=sys.stderr)
    index = {}
    rows = []
    for p in pdfs:
        try:
            txt = subprocess.run(["pdftotext", "-layout", str(p), "-"],
                                 capture_output=True, text=True, timeout=60).stdout
        except Exception as e:
            print(f"  FAIL {p.name}: {e}", file=sys.stderr)
            continue
        year, rnd = label_of(txt)
        label = f"{year} {rnd}" if year and rnd else None
        rows.append({"file": p.name, "year": year, "round": rnd, "label": label, "chars": len(txt)})
        if label and label not in index:
            index[label] = {"label": label, "year": year, "round": rnd, "file": p.name}
            (OUT / f"{label.replace(' ','_')}.txt").write_text(txt, encoding="utf-8")
    (OUT / "index.json").write_text(
        json.dumps(sorted(index.values(), key=lambda r:(r['year'],r['round'])),
                   ensure_ascii=False, indent=1), encoding="utf-8")
    # 진단
    labeled = [r for r in rows if r["label"]]
    print(f"라벨 식별: {len(labeled)}/{len(rows)}  유니크 시험: {len(index)}", file=sys.stderr)
    for r in rows:
        if not r["label"]:
            print(f"  UNLABELED {r['file']} year={r['year']} round={r['round']} chars={r['chars']}", file=sys.stderr)
    print(json.dumps(sorted(index.keys()), ensure_ascii=False), file=sys.stderr)

if __name__ == "__main__":
    main()
