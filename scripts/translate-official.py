#!/usr/bin/env python3
"""공식 단어장 Lv.1~12 의 뜻·어원을 다른 언어로 옮긴다.

영어 단어·발음기호·예문은 언어와 무관하므로 건드리지 않는다.
바꾸는 건 한국어로 된 base(뜻) / ctx(문맥 뜻) / etym(어원) 셋뿐이다.

왜 한국어만 보고 번역하지 않는가:
  '기간, 시기' 만 주면 period 인지 term 인지 모델이 모른다.
  그래서 영어 단어와 영어 예문을 같이 줘서 뜻을 고정시킨다.

쓰는 법 (터미널):
  cd ~/voca
  export SUPABASE_URL=https://ziatqkjlafucqtwshhla.supabase.co
  export SUPABASE_SECRET_KEY=...     # 대시보드 → Settings → API Keys → secret
                                     #  (sb_secret_… 로 시작. 옛 service_role JWT 는
                                     #   2026-10-24 에 비활성화됐다)
  export GEMINI_API_KEY=...          # Google AI Studio

  # 1) 품질 먼저 — DB 에 쓰지 않고 화면에만 보여준다
  python3 scripts/translate-official.py --lang zh --levels 1,5,9 --limit 20 --dry-run

  # 2) 괜찮으면 전체
  python3 scripts/translate-official.py --lang zh
  python3 scripts/translate-official.py --lang es
  python3 scripts/translate-official.py --lang ja

이미 번역된 단어는 건너뛴다. 중간에 끊겨도 다시 돌리면 이어서 한다.
"""
import argparse, json, os, sys, time, urllib.request, urllib.error

LANG_NAMES = {
    'zh': ('Simplified Chinese', '简体中文'),
    'es': ('Spanish', 'español'),
    'ja': ('Japanese', '日本語'),
    'en': ('English', 'English'),
    'fr': ('French', 'français'),
    'pt': ('Portuguese (Brazil)', 'português'),
    'de': ('German', 'Deutsch'),
    'vi': ('Vietnamese', 'Tiếng Việt'),
    'id': ('Indonesian', 'Bahasa Indonesia'),
}
MODEL = 'gemini-2.5-flash'


def die(msg):
    print('✗ ' + msg, file=sys.stderr)
    sys.exit(1)


def req(url, method='GET', body=None, headers=None, timeout=120):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method,
                               headers=headers or {})
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raise RuntimeError('HTTP %d — %s' % (e.code, e.read().decode()[:300]))


# ── Supabase ────────────────────────────────────────────────────────────
class DB:
    def __init__(self, url, key):
        self.url = url.rstrip('/')
        # 새 형식 키(sb_secret_…)는 JWT 가 아니다. Authorization: Bearer 자리에
        # 넣으면 JWT 로 파싱하려다 거부하는 경로가 있어서(엣지 함수가 그랬다)
        # 새 키는 apikey 로만 보낸다. 레거시 JWT 는 둘 다 보내던 대로 둔다.
        self.h = {'apikey': key, 'Content-Type': 'application/json',
                  'User-Agent': 'imvoca-translate/1.0'}
        if key.startswith('eyJ'):
            self.h['Authorization'] = 'Bearer ' + key

    def get(self, path):
        return req(self.url + '/rest/v1/' + path, headers=self.h)

    def upsert(self, table, rows):
        h = dict(self.h)
        h['Prefer'] = 'resolution=merge-duplicates,return=minimal'
        req(self.url + '/rest/v1/' + table, 'POST', rows, h)

    def page_all(self, path, step=1000):
        """PostgREST 는 한 번에 1000행까지만 준다 → offset 으로 끝까지 긁는다."""
        out, off = [], 0
        sep = '&' if '?' in path else '?'
        while True:
            chunk = self.get('%s%slimit=%d&offset=%d' % (path, sep, step, off))
            if not chunk:
                break
            out += chunk
            if len(chunk) < step:
                break
            off += step
        return out


def fetch_words(db, levels):
    books = db.get('voca_books?is_official=eq.true&select=id,description')
    want = {'IMV-L%d' % n for n in levels}
    ids = [b['id'] for b in books if (b.get('description') or '').strip().upper() in want]
    if not ids:
        die('Lv.%s 책을 못 찾았다 (description 이 IMV-L1 … IMV-L12 인지 확인)'
            % ','.join(map(str, levels)))
    pages = db.page_all('voca_pages?book_id=in.(%s)&select=id,book_id,page_num'
                        % ','.join(ids))
    lvl = {b['id']: (b.get('description') or '') for b in books}
    pmeta = {p['id']: (lvl.get(p['book_id'], ''), p.get('page_num', '')) for p in pages}
    words = db.page_all('voca_words?page_id=in.(%s)&select=id,en,base,ctx,sentence,analysis,page_id'
                        % ','.join(pmeta))
    for w in words:
        w['_lv'], w['_day'] = pmeta.get(w['page_id'], ('', ''))
    return words


# ── Gemini ──────────────────────────────────────────────────────────────
PROMPT = """You are localizing a vocabulary textbook for learners of English.

Each item has an English headword, an English example sentence, and Korean
glosses. Rewrite ONLY the Korean parts into {lang_en} ({lang_native}).

Rules:
- "base": the dictionary meaning(s) of the English headword. Keep the same
  number of senses, separated by a comma. Natural {lang_en}, not word-for-word
  Korean. Use the example sentence to pick the right sense.
- "ctx": the meaning as used in THAT sentence. If the input ctx is empty,
  return an empty string.
- "etym": the word-origin note. It breaks the English word into parts and
  glosses each part. Keep the same structure and the same arrow "→", but write
  the glosses in {lang_en}. Keep the Latin/Greek roots in Latin letters.
  If the input etym is empty, return an empty string.
- Do NOT translate the English headword or the example sentence.
- Do NOT add romanization, pronunciation, or commentary.

Return ONLY a JSON array, one object per item, same order, same length:
[{{"i":0,"base":"...","ctx":"...","etym":"..."}}]

Items:
{items}"""


def translate(api_key, lang, batch, retries=4):
    lang_en, lang_native = LANG_NAMES[lang]
    items = [{'i': n, 'en': w['en'], 'sentence': (w.get('sentence') or '')[:200],
              'base': w.get('base') or '',
              'ctx': w.get('ctx') or '',
              'etym': ((w.get('analysis') or {}).get('etym') or '')}
             for n, w in enumerate(batch)]
    prompt = PROMPT.format(lang_en=lang_en, lang_native=lang_native,
                           items=json.dumps(items, ensure_ascii=False))
    url = ('https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s'
           % (MODEL, api_key))
    body = {'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.2, 'responseMimeType': 'application/json'}}
    for attempt in range(retries):
        try:
            res = req(url, 'POST', body, {'Content-Type': 'application/json'})
            txt = res['candidates'][0]['content']['parts'][0]['text']
            arr = json.loads(txt)
            if not isinstance(arr, list):
                raise ValueError('배열이 아님')
            by_i = {int(o['i']): o for o in arr if 'i' in o}
            if len(by_i) != len(batch):
                raise ValueError('개수 불일치 %d≠%d' % (len(by_i), len(batch)))
            return [by_i[n] for n in range(len(batch))]
        except Exception as e:
            if attempt == retries - 1:
                raise
            wait = 2 ** attempt
            print('   재시도 %d/%d (%ss) — %s' % (attempt + 1, retries - 1, wait, str(e)[:90]))
            time.sleep(wait)


# ── main ────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', required=True, choices=sorted(LANG_NAMES))
    ap.add_argument('--levels', default=','.join(str(n) for n in range(1, 13)),
                    help='예: 1,5,9  (기본: 1~12 전부)')
    ap.add_argument('--limit', type=int, default=0, help='이 개수만 (0=전부)')
    ap.add_argument('--batch', type=int, default=25)
    ap.add_argument('--dry-run', action='store_true', help='DB 에 쓰지 않고 화면에만')
    ap.add_argument('--redo', action='store_true', help='이미 번역된 것도 다시')
    a = ap.parse_args()

    url = os.environ.get('SUPABASE_URL', '').strip()
    key = (os.environ.get('SUPABASE_SECRET_KEY', '')
           or os.environ.get('SERVICE_ROLE_KEY', '')).strip()
    gem = os.environ.get('GEMINI_API_KEY', '').strip()
    if not url or not key:
        die('SUPABASE_URL / SUPABASE_SECRET_KEY 를 환경변수로 넣어주세요')
    # 레거시 anon/service_role JWT 는 2026-10-24 에 비활성화했다(키 유출 대응).
    # 그대로 쓰면 첫 요청에서 401 이 나므로 여기서 먼저 잡아준다.
    if key.startswith('eyJ'):
        die('옛 service_role 키(JWT)입니다. 이 키는 비활성화돼 있어요.\n'
            '  Supabase 대시보드 → Settings → API Keys 에서\n'
            "  'secret' 키(sb_secret_… 로 시작)를 복사해 쓰세요.\n"
            '    export SUPABASE_SECRET_KEY=sb_secret_...')
    if key.startswith('sb_publishable_'):
        die('publishable(공개) 키입니다. 이 키로는 쓰기가 안 돼요.\n'
            "  Settings → API Keys 에서 'secret' 키를 복사해 쓰세요.")
    if not key.startswith('sb_secret_'):
        print('⚠ 키 형식이 sb_secret_… 가 아닙니다. 계속 시도합니다.')
    if not gem:
        die('GEMINI_API_KEY 를 환경변수로 넣어주세요')

    levels = [int(x) for x in a.levels.split(',') if x.strip()]
    db = DB(url, key)

    print('· 단어를 읽는 중…')
    words = fetch_words(db, levels)
    print('  Lv.%s → %d단어' % (a.levels, len(words)))

    if not a.redo:
        done = {r['word_id'] for r in
                db.page_all('voca_word_i18n?lang=eq.%s&select=word_id' % a.lang)}
        before = len(words)
        words = [w for w in words if w['id'] not in done]
        if before != len(words):
            print('  이미 번역됨 %d개 건너뜀 → 남은 %d개' % (before - len(words), len(words)))
    if a.limit:
        # 앞에서부터 자르면 Lv.1 만 뽑혀서 품질 확인이 안 된다
        # (기초 단어는 어원이 비어 있어 제일 어려운 부분을 못 본다).
        # 요청한 레벨에 고르게 퍼뜨리고, 어원이 있는 단어를 앞에 둔다.
        by_lv = {}
        for w in words:
            by_lv.setdefault(w['_lv'], []).append(w)
        for v in by_lv.values():
            v.sort(key=lambda w: 0 if ((w.get('analysis') or {}).get('etym')) else 1)
        picked, keys = [], sorted(by_lv, key=lambda k: int(k.split('-L')[-1] or 0))
        i = 0
        while len(picked) < a.limit and any(i < len(by_lv[k]) for k in keys):
            for k in keys:
                if i < len(by_lv[k]) and len(picked) < a.limit:
                    picked.append(by_lv[k][i])
            i += 1
        words = picked
    if not words:
        print('✓ 할 일이 없습니다.')
        return

    batches = [words[i:i + a.batch] for i in range(0, len(words), a.batch)]
    print('· %s 로 번역 — %d단어 / %d묶음%s\n'
          % (LANG_NAMES[a.lang][1], len(words), len(batches),
             '  (연습: DB 에 쓰지 않음)' if a.dry_run else ''))

    ok = fail = 0
    t0 = time.time()
    for bi, batch in enumerate(batches, 1):
        try:
            out = translate(gem, a.lang, batch)
        except Exception as e:
            fail += len(batch)
            print('✗ %d/%d 묶음 실패 — %s' % (bi, len(batches), str(e)[:140]))
            continue
        rows = []
        for w, o in zip(batch, out):
            base = (o.get('base') or '').strip()
            if not base:
                fail += 1
                continue
            rows.append({'word_id': w['id'], 'lang': a.lang, 'base': base,
                         'ctx': (o.get('ctx') or '').strip() or None,
                         'etym': (o.get('etym') or '').strip() or None})
            if a.dry_run:
                print('  %-16s %-8s %s' % (w['en'], w['_lv'], base))
                if o.get('etym'):
                    print('  %-16s %-8s   어원 %s' % ('', '', o['etym']))
        if rows and not a.dry_run:
            try:
                db.upsert('voca_word_i18n', rows)
            except Exception as e:
                fail += len(rows)
                print('✗ %d/%d 저장 실패 — %s' % (bi, len(batches), str(e)[:140]))
                continue
        ok += len(rows)
        if not a.dry_run:
            el = time.time() - t0
            eta = el / bi * (len(batches) - bi)
            print('  %d/%d 묶음 · %d단어 완료 · 남은 시간 약 %d분'
                  % (bi, len(batches), ok, eta / 60 + 0.5))

    print('\n%s 성공 %d · 실패 %d%s'
          % ('✓' if not fail else '△', ok, fail,
             '  (연습이라 저장하지 않음)' if a.dry_run else ''))
    if fail:
        print('  실패분은 같은 명령을 다시 돌리면 이어서 합니다.')


if __name__ == '__main__':
    main()
