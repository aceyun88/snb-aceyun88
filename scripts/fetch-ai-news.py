# 매주 월요일 아침, 믿을 만한 출처에서 한 주의 AI 소식을 모아 "한 주 한 게시글"로 ai-news.json에 쌓는다 (제목 = 그 주 가장 핵심인 첫 뉴스 제목)
# 출처: 조코딩 IT뉴스 라이브(유튜브) · GitHub 이번 주 인기 저장소 · 긱뉴스(GeekNews) 화제 글 · AI타임스 · 구글 뉴스(국내 매체, 플랫폼별)
# 요약문은 원문 제목·출처·수치(조회수·별·포인트)만 쓰고 지어내지 않는다.
import io, json, os, re, sys, html, datetime, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36', 'Accept-Language': 'ko-KR,ko;q=0.9'}
ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT = os.path.join(ROOT, 'ai-news.json')
KST = datetime.timezone(datetime.timedelta(hours=9))
NOW = datetime.datetime.now(KST)
TODAY = NOW.date()
WEEK_AGO = NOW - datetime.timedelta(days=7)

AI_WORDS = r'AI|인공지능|GPT|LLM|클로드|Claude|제미나이|Gemini|오픈AI|OpenAI|앤트로픽|Anthropic|코파일럿|Copilot|에이전트|Agent|모델|딥시크|DeepSeek|미스트랄|라마|Llama|바이브|MCP|프롬프트|생성형|퍼플렉시티|Perplexity|Grok|Sora|소라|나노바나나|휴머노이드|로봇'
RELEASE = r'공개|출시|발표|도입|업데이트|선보|내놓|정식|출간'
GOOD = ['지디넷', 'AI타임스', '전자신문', '디지털데일리', '조선비즈', '매일경제', '한국경제', '연합뉴스', '뉴시스', '머니투데이', '블로터', '테크월드',
        '보안뉴스', '뉴스탭', '디일렉', 'IT조선', '데일리안', '서울경제', '동아일보', '중앙일보', '아시아경제', '이데일리', 'ZDNet', '바이라인', '벤처스퀘어',
        '데브타임즈', '뉴스스페이스', '테크M', '더구루', '헤럴드경제', '파이낸셜뉴스', 'KBS', 'MBC', 'SBS', 'YTN', '한겨레', '경향', '국민일보',
        '뉴스1', '뉴스핌', '아이뉴스24', '인공지능신문', 'AI포스트', '씨넷', '디지털투데이', '스타트업투데이', '플래텀', '지피코리아', '글로벌이코노믹', '뉴스웨이']
BAD_TITLE = r'축구|감독|경기|선수|드라마|예능|아이돌|주가 급등|급락|테마주'
PLATFORMS = [
    ('OpenAI · 챗GPT', 'OpenAI OR 챗GPT OR ChatGPT'),
    ('앤트로픽 · 클로드', '앤트로픽 OR 클로드 OR Anthropic'),
    ('구글 · 제미나이', '제미나이 OR Gemini 구글'),
    ('마이크로소프트 · 코파일럿', '코파일럿 OR Copilot 마이크로소프트'),
    ('퍼플렉시티 · AI 검색', '퍼플렉시티 OR "AI 검색" OR "AI 모드"'),
    ('네이버 · 국내 AI', '네이버 AI OR 하이퍼클로바 OR "소버린 AI"'),
    ('이미지·영상 생성', '"이미지 생성" AI OR "영상 생성" AI OR 소라 OR 미드저니 OR 나노바나나'),
    ('AI 에이전트·자동화', '"AI 에이전트" OR "바이브 코딩" OR MCP AI'),
]

def fetch(url, extra=None):
    h = dict(UA); h.update(extra or {})
    return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=40).read()

def text(url, extra=None):
    return fetch(url, extra).decode('utf-8', 'ignore')

def clean(t):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t or ''))).strip()

def when(s):
    try:
        return parsedate_to_datetime(s).astimezone(KST)
    except Exception:
        try:
            return datetime.datetime.fromisoformat(s.strip()[:25]).astimezone(KST)
        except Exception:
            return None

def rss_items(url):
    root = ET.fromstring(fetch(url))
    out = []
    for it in root.findall('./channel/item'):
        src = it.find('source')
        out.append({'title': clean(it.findtext('title')), 'url': (it.findtext('link') or '').strip(),
                    'source': clean(src.text if src is not None else ''), 'at': when(it.findtext('pubDate') or '')})
    return out

items = []
def add(platform, title, url, source, note='', at=None):
    items.append({'platform': platform, 'title': title, 'url': url, 'source': source, 'note': note,
                  'at': at.strftime('%Y-%m-%d') if at else ''})

# 1. 조코딩 IT뉴스 라이브 — 가장 최근 방송 1건 (유튜브 채널 스트림 목록에서 "IT뉴스"로 시작하는 제목)
def jocoding():
    h = text('https://www.youtube.com/@jocoding/streams', {'Cookie': 'CONSENT=YES+1; SOCS=CAI'})
    d = json.loads(re.search(r'var ytInitialData = (\{.*?\});</script>', h, re.S).group(1))
    found = []
    def walk(o):
        if isinstance(o, dict):
            if 'lockupViewModel' in o:
                l = o['lockupViewModel']
                try:
                    md = l['metadata']['lockupMetadataViewModel']
                    parts = [p.get('text', {}).get('content', '') for r in md.get('metadata', {}).get('contentMetadataViewModel', {}).get('metadataRows', []) for p in r.get('metadataParts', [])]
                    found.append((l.get('contentId'), md['title']['content'], ' · '.join(p for p in parts if p)))
                except Exception:
                    pass
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(d)
    for vid, title, meta in found:
        if title.startswith('IT뉴스') and '예정일' not in meta:
            add('조코딩 IT뉴스 라이브 (유튜브)', title, f'https://www.youtube.com/watch?v={vid}', '조코딩', meta)
            return

# 2. GitHub 이번 주 인기 저장소 — 트렌딩(주간) 상위 8개
def github():
    h = text('https://github.com/trending?since=weekly')
    rows = []
    for a in h.split('<article class="Box-row">')[1:]:
        name = re.search(r'<h2 class="h3 lh-condensed">.*?href="/([^"]+)"', a, re.S)
        if not name: continue
        desc = re.search(r'<p class="col-9[^>]*>(.*?)</p>', a, re.S)
        desc = clean(desc.group(1)) if desc else ''
        wk = re.search(r'([\d,]+) stars this week', a)
        lang = re.search(r'itemprop="programmingLanguage">([^<]+)', a)
        rows.append((int(wk.group(1).replace(',', '')) if wk else 0, name.group(1), desc, lang.group(1) if lang else 'GitHub'))
    rows.sort(key=lambda r: -r[0])   # 이번 주 받은 별 순
    for stars, name, desc, lang in rows[:8]:
        add('GitHub 이번 주 인기 저장소', name + (' — ' + desc[:90] if desc else ''), 'https://github.com/' + name, lang, f'{stars:,} stars (이번 주)')

# 3. 긱뉴스(GeekNews) — 최근 7일 AI 관련 글을 포인트 순으로 8개
def geeknews():
    rows = []
    for page in range(1, 4):
        h = text('https://news.hada.io/' + (f'?page={page}' if page > 1 else ''))
        for b in h.split("class='topic_row'")[1:]:
            t = re.search(r"class='topic-title-heading'>(.*?)</h2>", b, re.S)
            tid = re.search(r'topic\?id=(\d+)', b)
            pts = re.search(r"id='tp\d+'>(\d+)</span>", b)
            dt = re.search(r'datetime="([^"]+)"', b)
            if not (t and tid and dt): continue
            at = when(dt.group(1))
            title = clean(t.group(1))
            if at and at >= WEEK_AGO and re.search(AI_WORDS, title, re.I):
                rows.append((int(pts.group(1)) if pts else 0, title, tid.group(1), at))
    rows.sort(key=lambda r: -r[0])
    for p, title, tid, at in rows[:8]:
        add('긱뉴스(GeekNews) 화제 글', title, f'https://news.hada.io/topic?id={tid}', 'GeekNews', f'{p} points', at)

# 4. AI타임스 — 최근 7일 기사 중 공개·출시·발표 보도를 앞세워 8개
def aitimes():
    rows = [it for it in rss_items('https://www.aitimes.com/rss/allArticle.xml') if it['at'] and it['at'] >= WEEK_AGO and not re.search(BAD_TITLE, it['title'])]
    rows.sort(key=lambda it: (0 if re.search(RELEASE, it['title']) else 1, -it['at'].timestamp()))
    for it in rows[:8]:
        add('AI타임스 주요 기사', it['title'], it['url'], 'AI타임스', '', it['at'])

# 5. 플랫폼별 국내 보도 — 구글 뉴스 7일, 믿을 만한 매체만, 플랫폼당 2건
def platforms():
    for plat, q in PLATFORMS:
        n = 0
        for it in rss_items('https://news.google.com/rss/search?q=' + urllib.parse.quote(q + ' when:7d') + '&hl=ko&gl=KR&ceid=KR:ko')[:15]:
            if not any(g in it['source'] for g in GOOD) or re.search(BAD_TITLE, it['title']): continue
            add(plat, re.sub(r'\s+-\s+[^-]{1,30}$', '', it['title']), it['url'], it['source'], '', it['at'])
            n += 1
            if n >= 2: break

for name, fn in [('조코딩', jocoding), ('GitHub', github), ('긱뉴스', geeknews), ('AI타임스', aitimes), ('플랫폼', platforms)]:
    try:
        fn()
    except Exception as e:
        print('skip', name, repr(e)[:120], file=sys.stderr)

# 제목 중복 제거
seen, week_items = set(), []
for it in items:
    key = re.sub(r'[^\w가-힣]', '', it['title'])[:40]
    if not it['title'] or key in seen: continue
    seen.add(key); week_items.append(it)

# 핵심 뉴스 = AI타임스·플랫폼 보도 가운데 "공개·출시·발표"가 있는 것 우선, 그다음 플랫폼 우선순위
order = {p[0]: i for i, p in enumerate(PLATFORMS)}
def score(it):
    if it['platform'] not in order and it['platform'] != 'AI타임스 주요 기사': return 99
    s = order.get(it['platform'], 6) * 2
    return s + (0 if re.search(RELEASE, it['title']) else 20)
head = min(week_items, key=score)['title'] if week_items else '이번 주는 새 소식이 없습니다'

label = f'{TODAY.year}년 {TODAY.month}월 {(TODAY.day - 1) // 7 + 1}주'
post = {'date': TODAY.isoformat(), 'label': label, 'title': head, 'count': len(week_items), 'items': week_items}
data = {'updated': TODAY.isoformat(), 'posts': []}
if os.path.exists(OUT):
    try: data = json.load(io.open(OUT, encoding='utf-8'))
    except Exception: pass
posts = [p for p in data.get('posts', []) if p.get('date') != post['date']]
posts.insert(0, post)
io.open(OUT, 'w', encoding='utf-8').write(json.dumps({'updated': TODAY.isoformat(), 'posts': posts[:26]}, ensure_ascii=False, indent=1))
print(label, post['count'], '건 →', head[:60])
for g in dict.fromkeys(it['platform'] for it in week_items):
    print('  ', g, sum(1 for it in week_items if it['platform'] == g))
