# 파이낸스투데이·소상공인뉴스에서 윤성임 박사의 칼럼·기사 목록을 모아 news.json을 만든다 (배포 전 실행: python scripts/fetch-news.py)
import io, json, re, sys, urllib.parse, urllib.request, html, os

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
ROOT = os.path.join(os.path.dirname(__file__), '..')

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', 'ignore')

def unesc(s):
    return html.unescape(re.sub(r'\s+', ' ', s)).strip()

items = {}

def add(url, title, date, source, series):
    key = url
    if key in items:
        return
    items[key] = {'title': title, 'date': date, 'url': url, 'source': source, 'series': series}

def series_of(title):
    m = re.match(r'\[([^\]]+)\]', title)
    if m:
        tag = m.group(1)
        if '소셜비즈테크' in tag: return '소셜비즈테크 칼럼'
        if 'AI리터러시' in tag or 'AI 리터러시' in tag: return 'AI 리터러시 칼럼'
        if 'AI융합비즈마케팅' in tag: return 'AI융합비즈마케팅 칼럼'
        if '인터뷰' in tag: return '현장 인터뷰'
        return tag
    return '기사'

# ── 1) 파이낸스투데이 — 검색어별 목록 (page 1~5)
FN = 'https://www.fntoday.co.kr'
for word in ['윤성임', '소셜비즈테크', '소셜앤비즈']:
    for page in range(1, 6):
        url = f'{FN}/news/articleList.html?sc_area=A&view_type=sm&sc_word={urllib.parse.quote(word)}&page={page}'
        try:
            h = get(url)
        except Exception as e:
            print('skip', url, e, file=sys.stderr); break
        rows = re.findall(r'class="list-titles"[^>]*>\s*<a href="([^"]+)"[^>]*>\s*<strong>([^<]+)</strong>.*?class="list-dated">([^<]+)</div>', h, re.S)
        if not rows:
            break
        for href, title, dated in rows:
            title = unesc(title)
            if not any(k in title for k in ['윤성임', '소셜앤비즈', '소셜비즈테크']):
                continue
            m = re.search(r'(\d{4}-\d{2}-\d{2})', dated)
            add(FN + href, title, m.group(1) if m else '', '파이낸스투데이', series_of(title))

# ── 2) 소상공인뉴스(sbma.kr) — 칼럼&인터뷰 목록 + 검색
SB = 'https://www.sbma.kr'
for url in [f'{SB}/news_gisa/gisa_list.htm?gisa_category=02000000&page={p}' for p in range(1, 4)] + [f'{SB}/news_gisa/gisa_list.htm?gisa_category=01000000&page={p}' for p in range(1, 3)]:
    try:
        h = get(url)
    except Exception as e:
        print('skip', url, e, file=sys.stderr); continue
    for href, title, date in re.findall(r'<a href="(/news_gisa/gisa_view\.htm[^"]+)">\s*<span class="figure">.*?<span class="title">([^<]+)</span>.*?<span class="date">([^<]*)</span>', h, re.S):
        title = unesc(title)
        if not any(k in title for k in ['윤성임', '소셜앤비즈', '소셜비즈테크']):
            continue
        m = re.search(r'(\d{4})[.\-/](\d{2})[.\-/](\d{2})', date)
        add(SB + html.unescape(href), title, f'{m.group(1)}-{m.group(2)}-{m.group(3)}' if m else date.strip(), '소상공인뉴스', series_of(title))

out = sorted(items.values(), key=lambda x: x['date'], reverse=True)
path = os.path.join(ROOT, 'news.json')
io.open(path, 'w', encoding='utf-8').write(json.dumps({'updated': __import__('datetime').date.today().isoformat(), 'items': out}, ensure_ascii=False, indent=1))
print(len(out), 'items →', os.path.abspath(path))
for it in out[:8]:
    print(it['date'], it['series'], '|', it['title'][:60])
