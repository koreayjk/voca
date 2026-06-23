#!/usr/bin/env python3
"""
각 단어의 실제 기출 문장 + 출처(연도/회차/문항번호)를 찾는다.
- corpus/index.json 의 48개 시험을 -raw(읽기순서)로 추출
- 독해영역 18~45번을 문항 단위로 분리 (raw는 문항번호가 단조증가 → 줄머리 'NN.' 앵커로 분리)
- 단어별로 문장 검색, 회차 골고루 분산되도록 후보 정렬
입력 단어목록: 인자로 받은 JSON(book 파일)의 words[].en
출력: occurrences.json  { word: [ {label, item, sentence}, ... ] }
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTDIR = (ROOT / ".." / ".." / "test").resolve()
CORPUS = ROOT / "corpus"

# 검색 stem(불규칙 변화 대응). 기본은 단어 그대로.
STEM = {
    "various":"vari", "value":"valu", "society":"societ", "create":"creat",
    "increase":"increas", "require":"requir", "believe":"believ", "reduce":"reduc",
    "improve":"improv", "company":"compan", "activity":"activit", "century":"centur",
    "nature":"natur", "future":"futur", "culture":"cultur", "science":"scien",
    "knowledge":"knowledg", "behavior":"behavior", "individual":"individual",
    "personal":"personal", "particular":"particular", "physical":"physical",
    "attention":"attention", "environment":"environment", "research":"research",
    "provide":"provid", "tend":"tend", "affect":"affect", "effect":"effect",
}

def stem_re(word):
    s = STEM.get(word, word)
    return re.compile(r"\b" + re.escape(s) + r"[a-z]*", re.I)

def split_items(raw):
    """raw 텍스트에서 18~45번 문항을 (num, text)로 분리."""
    lines = raw.split("\n")
    items = {}
    cur = None
    buf = []
    anchor = re.compile(r"^\s*(\d{1,2})\.\s")
    for ln in lines:
        m = anchor.match(ln)
        if m:
            n = int(m.group(1))
            if 18 <= n <= 45 and (cur is None or n >= cur):  # 단조증가만 인정
                if cur is not None:
                    items[cur] = "\n".join(buf)
                cur = n
                buf = [ln]
                continue
        if cur is not None:
            buf.append(ln)
    if cur is not None:
        items[cur] = "\n".join(buf)
    return items

def sentences(text):
    # 문항 마크업/선택지/각주 제거 후 영어 문장 단위 분리
    t = re.sub(r"^\s*\d{1,2}\.\s.*?(?=\n)", "", text, count=1)  # 문항 지시문 첫줄 제거
    t = t.replace("\n", " ")
    t = re.sub(r"\[\d점\]", " ", t)
    t = re.sub(r"[①②③④⑤].*", "", t)     # 선택지 이후 컷
    t = re.sub(r"\*[^*]+", " ", t)          # 각주(* glossary) 컷
    t = re.sub(r"\s+", " ", t).strip()
    # 문장분리
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z“\"])", t)
    return [p.strip() for p in parts if len(p.split()) >= 5]

def main():
    book = json.load(open(sys.argv[1]))
    words = [w["en"] for w in book["words"]]
    index = json.load(open(CORPUS / "index.json"))

    exams = []  # (label, items dict)
    for row in index:
        pdf = TESTDIR / row["file"]
        raw = subprocess.run(["pdftotext","-raw",str(pdf),"-"],
                             capture_output=True,text=True,timeout=60).stdout
        exams.append((row["label"], split_items(raw)))

    def clean(s):
        # 깨끗한 완결 문장 점수: 대문자 시작, 빈칸/슬래시선택지 없음, 적정 길이
        bad = ("____" in s) or (" / " in s) or s[0].islower()
        n = len(s.split())
        fit = 7 <= n <= 28
        return (0 if bad else 1, 1 if fit else 0, -abs(16-n))

    out = {}
    for w in words:
        rx = stem_re(w)
        by_label = {}   # label -> best sentence info
        total = 0
        for label, items in exams:
            for num, text in items.items():
                for s in sentences(text):
                    if rx.search(s):
                        total += 1
                        cand = {"label":label,"item":num,"sentence":s}
                        if label not in by_label or clean(s) > clean(by_label[label]["sentence"]):
                            by_label[label] = cand
        cands = sorted(by_label.values(), key=lambda c:c["label"])
        out[w] = {"count":total, "exams":len(by_label), "cands":cands}
    Path(CORPUS/"occurrences.json").write_text(
        json.dumps(out,ensure_ascii=False,indent=1),encoding="utf-8")
    # 요약
    for w in words:
        print(f"{w:14s} hits={out[w]['count']:3d} exams={out[w]['exams']:2d}")

if __name__=="__main__":
    main()
