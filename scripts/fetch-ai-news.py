# 대표 생성형 AI 플랫폼 소식을 모아 "하루 한 게시글"로 정리해 ai-news.json에 쌓는다 (제목 = 그날 가장 핵심인 첫 뉴스 제목)
# 출처: 구글 뉴스 RSS(국내 기사, 한국어) + 공식 블로그 RSS(OpenAI·구글 딥마인드) + AI타임스. 요약문은 기사 제목·출처만 쓰고 지어내지 않는다.
import io, json, os, re, sys, html, datetime, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36'}
ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT = os.path.join(ROOT, 'ai-news.json')
KST = datetime.timezone(datetime.timedelta(hours=9))
TODAY = datetime.datetime.now(KST).date()

# 플랫폼별 검색어 — 우선순위 순서(핵심 뉴스 제목을 고를 때 앞 플랫폼부터)
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
OFFICIAL = [
    ('OpenAI 공식', 'https://openai.com/news/rss.xml'),
    ('구글 딥마인드 공식', 'https://deepmind.google/blog/rss.xml'),
    ('AI타임스', 'https://www.aitimes.com/rss/allArticle.xml'),
]

# 믿을 만한 국내 매체만 (구글 뉴스에는 스팸·번역 사이트가 섞인다)
GOOD = ['지디넷', 'AI타임스', '전자신문', '디지털데일리', '조선비즈', '매일경제', '한국경제', '연합뉴스', '뉴시스', '머니투데이', '블로터', '테크월드',
        '보안뉴스', '뉴스탭', '디일렉', 'IT조선', '데일리안', '서울경제', '동아일보', '중앙일보', '아시아경제', '이데일리', 'ZDNet', '바이라인', '벤처스퀘어',
        '데브타임즈', '뉴스스페이스', '테크M', '더구루', '헤럴드경제', '파이낸셜뉴스', '전자신문', 'KBS', 'MBC', 'SBS', 'YTN', '한겨레', '경향', '국민일보',
        '뉴스1', '뉴스핌', '아이뉴스24', '인공지능신문', 'AI포스트', '씨넷', '디지털투데이', '스타트업투데이', '플래텀', '지피코리아', '글로벌이코노믹', '뉴스웨이']
BAD_TITLE = r'축구|감독|경기|선수|모레노|팬心|드라마|예능|아이돌|주가 급등|급락|테마주'

def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()

def when(s):
    try:
        return parsedate_to_datetime(s).astimezone(KST)
    except Exception:
        try:
            return datetime.datetime.fromisoformat(s.strip()[:19]).replace(tzinfo=KST)
        except Exception:
            return None

def clean(t):
    t = html.unescape(re.sub(r'\s+', ' ', t or '')).strip()
    return t

def rss_items(url):
    root = ET.fromstring(fetch(url))
    out = []
    for it in root.findall('./channel/item'):
        d = when(it.findtext('pubDate') or it.findtext('{http://purl.org/dc/elements/1.1/}date') or '')
        src = it.find('source')
        out.append({'title': clean(it.findtext('title')), 'url': (it.findtext('link') or '').strip(), 'source': clean(src.text if src is not None else ''), 'at': d})
    return out

items = []
for plat, q in PLATFORMS:
    try:
        for it in rss_items('https://news.google.com/rss/search?q=' + urllib.parse.quote(q + ' when:1d') + '&hl=ko&gl=KR&ceid=KR:ko')[:12]:
            t = it['title']
            if not any(g in it['source'] for g in GOOD) or re.search(BAD_TITLE, t):
                continue
            # 구글 뉴스 제목은 " - 매체명"이 뒤에 붙는다
            t = re.sub(r'\s+-\s+[^-]{1,30}$', '', t)
            if sum(1 for x in items if x['platform'] == plat) >= 5:
                break
            items.append({'platform': plat, 'title': t, 'url': it['url'], 'source': it['source'], 'at': it['at']})
    except Exception as e:
        print('skip', plat, e, file=sys.stderr)
for name, url in OFFICIAL:
    try:
        for it in rss_items(url)[:5]:
            if it['at'] and (TODAY - it['at'].date()).days <= 2:
                items.append({'platform': name, 'title': it['title'], 'url': it['url'], 'source': name, 'at': it['at']})
    except Exception as e:
        print('skip', name, e, file=sys.stderr)

# 오늘(어제 06:30 이후) 것만, 제목 중복 제거
seen, today_items = set(), []
for it in items:
    key = re.sub(r'[^\w가-힣]', '', it['title'])[:40]
    if not it['title'] or key in seen:
        continue
    seen.add(key)
    today_items.append({'platform': it['platform'], 'title': it['title'], 'source': it['source'], 'url': it['url'], 'at': it['at'].strftime('%Y-%m-%d %H:%M') if it['at'] else ''})

# 핵심 뉴스 = 우선순위 플랫폼의 가장 최근 기사 중 제목에 "공개·출시·발표"가 있는 것 우선
def score(it):
    order = {p[0]: i for i, p in enumerate(PLATFORMS)}
    # "공개·출시·발표" 같은 사실 보도를 먼저, 그다음 플랫폼 우선순위, 공식 발표 가산
    s = order.get(it['platform'], 12) * 2
    s += 0 if re.search(r'공개|출시|발표|도입|업데이트|선보|내놓', it['title']) else 20
    if it['source'].startswith(('OpenAI', '구글 딥마인드')): s -= 3
    return s
today_items.sort(key=score)
head = today_items[0]['title'] if today_items else '오늘은 새 소식이 없습니다'

post = {'date': TODAY.isoformat(), 'title': head, 'count': len(today_items), 'items': today_items}
data = {'updated': TODAY.isoformat(), 'posts': []}
if os.path.exists(OUT):
    try:
        data = json.load(io.open(OUT, encoding='utf-8'))
    except Exception:
        pass
posts = [p for p in data.get('posts', []) if p.get('date') != post['date']]
posts.insert(0, post)
data = {'updated': TODAY.isoformat(), 'posts': posts[:90]}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1))
print(post['date'], post['count'], '건 →', head[:60])
for it in today_items[:6]:
    print('  ', it['platform'], '|', it['title'][:50], '|', it['source'])
