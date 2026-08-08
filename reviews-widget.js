/* IM VOCA — 랜딩페이지 후기 위젯
 * 앱 [🎉 이벤트]에 등록된 후기(voca_reviews)를 랜딩페이지에도 동일하게 노출.
 * 사용법: 페이지에 <div id="lp-reviews"></div> 를 두고 이 스크립트를 로드.
 * - 게시된 후기만 표시(RLS published=true), 당첨(후기/영상 등수) 우선 → 최신순.
 * - 10개씩 "더 보기". 영상은 성능을 위해 '클릭 시 재생'.
 */
(function () {
  var SB_URL = 'https://ziatqkjlafucqtwshhla.supabase.co';
  var SB_KEY = 'sb_publishable_anybo402FSdDKMNiWcQzSA_oc7LIzZC';
  var box = document.getElementById('lp-reviews');
  if (!box) return;
  var PAGE = 10, all = [], shown = 0;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function medal(n) { return { 1: '🥇', 2: '🥈', 3: '🥉' }[n] || ''; }

  // 링크 → 임베드 소스 (유튜브/인스타/틱톡). 없으면 null.
  function embed(url) {
    url = String(url || '').trim(); var m;
    if ((m = url.match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|shorts\/|embed\/|live\/))([\w-]{6,})/)))
      return { type: 'yt', src: 'https://www.youtube.com/embed/' + m[1] };
    if ((m = url.match(/instagram\.com\/(reel|p|tv)\/([\w-]+)/)))
      return { type: 'ig', src: 'https://www.instagram.com/' + m[1] + '/' + m[2] + '/embed' };
    if ((m = url.match(/tiktok\.com\/.*?\/video\/(\d+)/)) || (m = url.match(/tiktok\.com\/t\/(\w+)/)))
      return { type: 'tt', src: 'https://www.tiktok.com/embed/v2/' + m[1] };
    return null;
  }

  // 클릭 시 iframe 교체 (초기 로딩 부담 없이)
  window._lpPlay = function (btn, src, type) {
    var h;
    if (type === 'yt') {
      h = '<div style="position:relative;width:100%;padding-top:56.25%;border-radius:12px;overflow:hidden;background:#000;">'
        + '<iframe src="' + src + '?autoplay=1" style="position:absolute;inset:0;width:100%;height:100%;border:0;" allow="autoplay;encrypted-media;picture-in-picture" allowfullscreen></iframe></div>';
    } else {
      var w = type === 'tt' ? '325px' : '360px', ht = type === 'tt' ? '700px' : '640px';
      h = '<div style="display:flex;justify-content:center;"><iframe src="' + src + '" style="width:100%;max-width:' + w + ';height:' + ht + ';border:0;border-radius:12px;background:#fff;" scrolling="no" allowtransparency="true" allowfullscreen></iframe></div>';
    }
    btn.outerHTML = h;
  };

  function card(r) {
    var rRank = (r.rank >= 1 && r.rank <= 3) ? r.rank : 0;
    var vRank = (r.video_rank >= 1 && r.video_rank <= 3) ? r.video_rank : 0;
    var win = rRank || vRank;
    var date = ''; try { date = new Date(r.created_at).toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' }); } catch (e) {}
    var badges = '';
    if (rRank) badges += '<span style="background:#8b7ff0;color:#fff;font-size:11px;font-weight:800;padding:2px 9px;border-radius:99px;">✍️ 후기 ' + rRank + '등</span> ';
    if (vRank) badges += '<span style="background:#e0a731;color:#3a2b00;font-size:11px;font-weight:800;padding:2px 9px;border-radius:99px;">🎬 영상 ' + vRank + '등</span> ';
    var vid = '';
    var em = embed(r.link);
    if (em) {
      vid = '<div style="margin-top:12px;"><button onclick="_lpPlay(this,\'' + em.src + '\',\'' + em.type + '\')" style="display:flex;align-items:center;justify-content:center;gap:9px;width:100%;background:#16110a;color:#fff;border:none;border-radius:12px;padding:15px;font-size:14px;font-weight:700;cursor:pointer;">▶ 영상 후기 재생</button></div>';
    } else if (r.link) {
      vid = '<a href="' + esc(r.link) + '" target="_blank" rel="noopener" style="display:inline-block;margin-top:10px;color:#c79e52;font-weight:700;font-size:13px;text-decoration:none;">▶ 영상 후기 보기 →</a>';
    }
    return '<div style="border:1px solid ' + (win ? '#e0a731' : 'rgba(0,0,0,0.10)') + ';background:' + (win ? 'linear-gradient(180deg,#fffaf0,#fff)' : '#fff') + ';border-radius:16px;padding:18px;margin-bottom:14px;box-shadow:0 6px 18px rgba(42,32,23,0.06);">'
      + '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">'
      + (win ? '<span style="font-size:20px;">' + medal(Math.min(rRank || 9, vRank || 9)) + '</span>' : '')
      + '<b style="font-size:15px;color:#2a2017;">' + esc(r.user_name || '익명') + '</b>'
      + '<span style="margin-left:auto;font-size:12px;color:#9a8f80;">' + date + '</span></div>'
      + (badges ? '<div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap;">' + badges + '</div>' : '')
      + (r.body ? '<div style="font-size:14.5px;color:#3a2f24;line-height:1.7;margin-top:10px;white-space:pre-wrap;word-break:break-word;">' + esc(r.body) + '</div>' : '')
      + vid + '</div>';
  }

  function renderMore() {
    var moreWrap = document.getElementById('lp-reviews-more');
    if (moreWrap) moreWrap.remove();
    var next = all.slice(shown, shown + PAGE);
    box.insertAdjacentHTML('beforeend', next.map(card).join(''));
    shown += next.length;
    if (shown < all.length) {
      box.insertAdjacentHTML('afterend',
        '<div id="lp-reviews-more" style="text-align:center;margin-top:6px;"><button onclick="_lpMore()" style="background:none;border:1px solid rgba(0,0,0,0.16);border-radius:99px;padding:11px 26px;font-size:14px;font-weight:700;color:#2a2017;cursor:pointer;">후기 더 보기 (+' + Math.min(PAGE, all.length - shown) + ')</button></div>');
    }
  }
  window._lpMore = renderMore;

  function sortR(a, b) {
    var ba = Math.min(a.rank || 99, a.video_rank || 99), bb = Math.min(b.rank || 99, b.video_rank || 99);
    if (ba !== bb) return ba - bb;
    return new Date(b.created_at) - new Date(a.created_at);
  }

  fetch(SB_URL + '/rest/v1/voca_reviews?select=*&order=created_at.desc&limit=100',
    { headers: { apikey: SB_KEY, Authorization: 'Bearer ' + SB_KEY } })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (!Array.isArray(data) || !data.length) {
        box.innerHTML = '<div style="text-align:center;color:#9a8f80;padding:24px 0;font-size:14px;">첫 후기를 기다리고 있어요 🙌</div>';
        return;
      }
      all = data.sort(sortR); box.innerHTML = ''; shown = 0; renderMore();
    })
    .catch(function () {
      box.innerHTML = '<div style="text-align:center;color:#9a8f80;padding:24px 0;font-size:14px;">후기를 불러오지 못했어요.</div>';
    });
})();
