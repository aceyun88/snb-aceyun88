# 매일 아침, 지난 하루의 생성형 AI 소식을 공식 출처(OpenAI·Anthropic·Google) 우선으로 10건만 골라 ai-daily.json에 쌓는다 (주간 게시글 fetch-ai-news.py와 별개, 같은 소식은 주소로 걸러 14일 보관)
# 고르는 순서: ① 출처 층(공식 발표 → 국내 전문 매체·긱뉴스) ② 플랫폼 관련 낱말(에이전트·프롬프트·교육·리터러시·도구 기능) ③ 최신. 요약 문장은 지어내지 않고 출처의 설명·og:description만 옮긴다(영문은 무료 번역).
import io, json, os, re, sys, html, datetime, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36', 'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8'}
ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT = os.path.join(ROOT, 'ai-daily.json')
KST = datetime.timezone(datetime.timedelta(hours=9))
NOW = datetime.datetime.now(KST)
TODAY = NOW.date()
SINCE = NOW - datetime.timedelta(hours=36)   # 어제 아침 이후(시차·수집 지연을 감안해 36시간)
KEEP_DAYS = 14
PICK = 10
DEEPL_KEY = os.environ.get('DEEPL_API_KEY', '').strip()

AI_WORDS = r'AI|인공지능|GPT|LLM|클로드|Claude|제미나이|Gemini|오픈AI|OpenAI|앤트로픽|Anthropic|코파일럿|Copilot|에이전트|Agent|미스트랄|Mistral|라마|Llama|MCP|프롬프트|Prompt|생성형|Generative|퍼플렉시티|Perplexity|Sora|나노바나나|미드저니|노트북LM|NotebookLM|Codex|Claude Code|챗봇|RAG|모델|Model|Veo|Imagen|Gemma|음성|TTS|자동화|Automation|Skill|스킬|Workspace|Canvas|Deep Research'
EXCLUDE = r'국방|군사|무기|전쟁|주가|테마주|급등|급락|시총|소송|고소|법정|판결|인수합병|M&A|투자 유치|펀딩|반도체|HBM|GPU 수출|데이터센터|전력|원전|채용|해고|감원|파업|축구|경기|선수|드라마|예능|아이돌|weather|날씨'
# 우리 플랫폼(AI 교육·프롬프트·소상공인 활용)과 가까운 낱말 — 같은 층 안에서 앞세운다
PLATFORM_WORDS = r'에이전트|Agent|프롬프트|Prompt|교육|학습|Education|Learn|리터러시|literacy|Claude Code|Codex|Gemini app|제미나이 앱|Gems|Canvas|Deep Research|NotebookLM|노트북LM|Workspace|무료|free|학생|student|교사|teacher|Skill|스킬|MCP|커넥터|Connector|소상공인|business|Projects|프로젝트|메모리|memory|모델|model|출시|launch|Introducing|공개|release'
RELEASE = r'공개|출시|발표|도입|업데이트|선보|내놓|정식|release|launch|announc|introduc|available|new '

def fetch(url, extra=None):
    h = dict(UA); h.update(extra or {})
    return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=40).read()

def text(url, extra=None):
    return fetch(url, extra).decode('utf-8', 'ignore')

def clean(t):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t or ''))).strip()

def cut(t, n):
    t = clean(t)
    return t if len(t) <= n else t[:n].rsplit(' ', 1)[0] + '…'

def when(s):
    s = (s or '').strip()
    if not s: return None
    try:
        return parsedate_to_datetime(s).astimezone(KST)
    except Exception:
        pass
    try:
        return datetime.datetime.fromisoformat(s.replace('Z', '+00:00')[:25]).astimezone(KST)
    except Exception:
        return None

def rss_items(url):
    """RSS 2.0과 Atom 둘 다 읽는다"""
    root = ET.fromstring(fetch(url))
    out = []
    for it in root.iter():
        tag = it.tag.split('}')[-1]
        if tag not in ('item', 'entry'): continue
        def f(name):
            for c in it:
                if c.tag.split('}')[-1] == name: return c
            return None
        link = f('link')
        url_ = (link.text or '').strip() if link is not None and link.text else (link.get('href', '') if link is not None else '')
        date = None
        for n in ('pubDate', 'published', 'updated', 'date'):
            e = f(n)
            if e is not None and e.text: date = when(e.text); break
        desc = f('description') if f('description') is not None else f('summary')
        out.append({'title': clean(f('title').text if f('title') is not None else ''), 'url': url_, 'at': date,
                    'desc': clean(desc.text if desc is not None and desc.text else '')})
    return out

def og(url, prop):
    try:
        h = text(url)
        m = re.search(r'<meta[^>]+(?:property|name)=["\']' + prop + r'["\'][^>]+content=["\']([^"\']+)', h, re.I) or \
            re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']' + prop + r'["\']', h, re.I)
        return clean(m.group(1)) if m else ''
    except Exception:
        return ''

# 무료 번역이 자주 틀리는 고유명사 — 번역 뒤에 바로잡는다
BRAND_FIX = [('끌로드', '클로드'), ('클라우드 코드', '클로드 코드'), ('클라우드(Claude)', '클로드'), ('제미니', '제미나이'), ('앤트로피크', '앤트로픽'), ('안트로픽', '앤트로픽'),
             ('오픈에이아이', 'OpenAI'), ('오픈아이', 'OpenAI'), ('챗지피티', '챗GPT'), ('오푸스', 'Opus'), ('소네트', 'Sonnet'), ('하이쿠', 'Haiku'), ('딥마인드', '딥마인드')]

def fix_brands(t):
    for a, b in BRAND_FIX:
        t = t.replace(a, b)
    return t

def translate(en):
    """영문 한 줄을 한국어로. DeepL 무료(키 있을 때) → MyMemory 무료 → 실패하면 빈 문자열"""
    en = clean(en)[:300]
    if not en or not re.search(r'[A-Za-z]{3}', en) or re.search(r'[가-힣]', en): return ''
    try:
        if DEEPL_KEY:
            body = urllib.parse.urlencode({'text': en, 'target_lang': 'KO', 'source_lang': 'EN'}).encode()
            r = urllib.request.urlopen(urllib.request.Request('https://api-free.deepl.com/v2/translate', data=body,
                                       headers={'Authorization': 'DeepL-Auth-Key ' + DEEPL_KEY}), timeout=30).read()
            return fix_brands(clean(json.loads(r)['translations'][0]['text']))
        r = json.loads(text('https://api.mymemory.translated.net/get?q=' + urllib.parse.quote(en) + '&langpair=en|ko'))
        t = r.get('responseData', {}).get('translatedText', '')
        return '' if not t or 'MYMEMORY WARNING' in t.upper() else fix_brands(clean(t))
    except Exception:
        return ''

def ai_related(*texts):
    t = ' '.join(x for x in texts if x)
    return bool(re.search(AI_WORDS, t, re.I)) and not re.search(EXCLUDE, t, re.I)

items = []
def add(tier, source, title, url, at, desc='', lang='ko'):
    if not title or not url: return
    items.append({'tier': tier, 'source': source, 'title': title, 'url': url, 'at': at, 'desc': desc, 'lang': lang})

# ── 1층 공식 발표 ────────────────────────────────────────────────
OFFICIAL_RSS = [
    ('OpenAI 공식', 'https://openai.com/news/rss.xml'),
    ('구글 AI 블로그', 'https://blog.google/technology/ai/rss/'),
    ('구글 제미나이 블로그', 'https://blog.google/products/gemini/rss/'),
    ('구글 딥마인드 블로그', 'https://deepmind.google/blog/rss.xml'),
    ('구글 개발자 블로그', 'https://developers.googleblog.com/feeds/posts/default?alt=rss'),
]

def official_rss():
    for name, url in OFFICIAL_RSS:
        try:
            for it in rss_items(url):
                if it['at'] and it['at'] >= SINCE and ai_related(it['title'], it['desc']):
                    add(1, name, it['title'], it['url'], it['at'], cut(it['desc'], 200), 'en')
        except Exception as e:
            print('skip', name, repr(e)[:100], file=sys.stderr)

def anthropic_news(prev_urls):
    """앤트로픽은 RSS가 없어 뉴스 목록 페이지의 글 주소를 읽고, 전에 본 적 없는 글만 새 글로 친다(글 페이지의 발행일로 확인)"""
    try:
        h = text('https://www.anthropic.com/news')
    except Exception as e:
        print('skip Anthropic', repr(e)[:100], file=sys.stderr); return
    links = []
    for m in re.finditer(r'href="(/news/[a-z0-9\-]+)"', h):
        u = 'https://www.anthropic.com' + m.group(1)
        if u not in links: links.append(u)
    n = 0
    for u in links[:25]:
        if u in prev_urls: continue
        title = og(u, 'og:title')
        if not title: continue
        at = when(og(u, 'article:published_time')) or None
        if at and at < SINCE: continue
        if not at and n >= 3: break            # 날짜를 못 읽으면 앞쪽 3건까지만 새 글로 본다
        add(1, '앤트로픽 공식', re.sub(r'\s*\\\s*Anthropic$', '', title), u, at or NOW, cut(og(u, 'og:description'), 200), 'en')
        n += 1
        if n >= 6: break

# ── 2층 국내 전문 매체·커뮤니티 ───────────────────────────────────
def aitimes():
    try:
        for it in rss_items('https://www.aitimes.com/rss/allArticle.xml'):
            if it['at'] and it['at'] >= SINCE and ai_related(it['title'], it['desc']):
                add(2, 'AI타임스', it['title'], it['url'], it['at'], cut(it['desc'], 200))
    except Exception as e:
        print('skip AI타임스', repr(e)[:100], file=sys.stderr)

def geeknews():
    try:
        h = text('https://news.hada.io/')
    except Exception as e:
        print('skip 긱뉴스', repr(e)[:100], file=sys.stderr); return
    for b in h.split("class='topic_row'")[1:]:
        t = re.search(r"class='topic-title-heading'>(.*?)</h2>", b, re.S)
        tid = re.search(r'topic\?id=(\d+)', b)
        dt = re.search(r'datetime="([^"]+)"', b)
        if not (t and tid and dt): continue
        at = when(dt.group(1)); title = clean(t.group(1))
        if at and at >= SINCE and ai_related(title):
            add(2, '긱뉴스', title, f'https://news.hada.io/topic?id={tid.group(1)}', at)

# ── 모아서 10건 고르기 ─────────────────────────────────────────────
data = {'updated': '', 'days': []}
if os.path.exists(OUT):
    try: data = json.load(io.open(OUT, encoding='utf-8'))
    except Exception: pass
prev_urls = {it['url'] for d in data.get('days', []) if d.get('date') != TODAY.isoformat() for it in d.get('items', [])}   # 같은 날 다시 돌리면 오늘 것은 새로 고른다

official_rss()
anthropic_news(prev_urls)
aitimes()
geeknews()

seen, fresh = set(prev_urls), []
for it in items:
    key = re.sub(r'[^\w가-힣]', '', it['title'])[:40]
    if it['url'] in seen or key in seen: continue
    seen.add(it['url']); seen.add(key); fresh.append(it)

def score(it):
    t = it['title'] + ' ' + (it['desc'] or '')
    hits = len(re.findall(PLATFORM_WORDS, t, re.I))
    rel = 1 if re.search(RELEASE, it['title'], re.I) else 0
    ts = it['at'].timestamp() if it['at'] else 0
    return (-it['tier'], rel, hits, ts)

fresh.sort(key=score, reverse=True)
# 한 출처가 10건을 다 차지하지 않게 — 출처당 최대 4건
per, picked = {}, []
for it in fresh:
    if per.get(it['source'], 0) >= 4: continue
    per[it['source']] = per.get(it['source'], 0) + 1
    picked.append(it)
    if len(picked) >= PICK: break

for it in picked:
    if it['lang'] == 'en':
        ko = translate(it['title'])
        if ko:
            it['title_en'] = it['title']; it['title'] = ko
        dko = translate(it['desc']) if it['desc'] else ''
        if dko: it['desc_en'] = it['desc']; it['desc'] = dko
    it['at'] = it['at'].strftime('%Y-%m-%d %H:%M') if it['at'] else ''
    it.pop('lang', None)

day = {'date': TODAY.isoformat(), 'count': len(picked), 'items': picked}
days = [d for d in data.get('days', []) if d.get('date') != day['date']]
if picked or not days:
    days.insert(0, day)
cutoff = (TODAY - datetime.timedelta(days=KEEP_DAYS)).isoformat()
days = [d for d in days if d.get('date', '') >= cutoff]
io.open(OUT, 'w', encoding='utf-8').write(json.dumps({'updated': TODAY.isoformat(), 'days': days}, ensure_ascii=False, indent=1))
print(TODAY, len(picked), '건 (후보', len(fresh), ')')
for it in picked:
    print(f"  [{it['tier']}] {it['source']} · {it['title'][:60]}")
