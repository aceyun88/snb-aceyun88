# 매주 월요일 아침, 믿을 만한 출처에서 한 주의 생성형 AI 활용 소식을 모아 "한 주 한 게시글"로 ai-news.json에 쌓는다
# 출처: 조코딩 IT뉴스 라이브(유튜브) · GitHub 이번 주 인기 저장소 · 긱뉴스(GeekNews) 화제 글 · AI타임스 · 구글 뉴스(국내 매체, 플랫폼별)
# 정리 방식(A안, 2026-09-04): 생성형 AI 활용 낱말에 걸리는 것만 남기고, 낱말 표로 주제를 묶어 최대 10개 주제로 보여 준다.
# 요약 문장은 지어내지 않는다 — 긱뉴스 본문 첫 부분·AI타임스 og:description·GitHub 저장소 설명(무료 번역)만 옮긴다.
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
DEEPL_KEY = os.environ.get('DEEPL_API_KEY', '').strip()

# 생성형 AI "활용" 소식만 — 이 낱말 가운데 하나는 걸려야 하고, 제외 낱말에는 걸리지 않아야 한다
AI_WORDS = r'AI|인공지능|GPT|LLM|클로드|Claude|제미나이|Gemini|오픈AI|OpenAI|앤트로픽|Anthropic|코파일럿|Copilot|에이전트|Agent|딥시크|DeepSeek|미스트랄|Mistral|라마|Llama|바이브|Vibe|MCP|프롬프트|Prompt|생성형|Generative|퍼플렉시티|Perplexity|Grok|Sora|소라|나노바나나|미드저니|Midjourney|노트북LM|NotebookLM|커서|Cursor|Codex|코덱스|Claude Code|클로드 코드|챗봇|Chatbot|RAG|파인튜닝|모델|Model|Diffusion|이미지 생성|영상 생성|음성|TTS|Whisper|자동화|Automation|Skill|스킬'
EXCLUDE = r'국방|군사|무기|전쟁|주가|테마주|급등|급락|시총|소송|고소|법정|판결|규제안|법안|인수합병|M&A|투자 유치|펀딩|반도체|칩\b|HBM|GPU 수출|데이터센터|전력|원전|채용|해고|감원|파업|축구|감독|경기|선수|드라마|예능|아이돌'
RELEASE = r'공개|출시|발표|도입|업데이트|선보|내놓|정식|출간|release|launch|announc|introduc'
GOOD = ['지디넷', 'AI타임스', '전자신문', '디지털데일리', '조선비즈', '매일경제', '한국경제', '연합뉴스', '뉴시스', '머니투데이', '블로터', '테크월드',
        '보안뉴스', '뉴스탭', '디일렉', 'IT조선', '데일리안', '서울경제', '동아일보', '중앙일보', '아시아경제', '이데일리', 'ZDNet', '바이라인', '벤처스퀘어',
        '데브타임즈', '뉴스스페이스', '테크M', '더구루', '헤럴드경제', '파이낸셜뉴스', 'KBS', 'MBC', 'SBS', 'YTN', '한겨레', '경향', '국민일보',
        '뉴스1', '뉴스핌', '아이뉴스24', '인공지능신문', 'AI포스트', '씨넷', '디지털투데이', '스타트업투데이', '플래텀', '지피코리아', '글로벌이코노믹', '뉴스웨이']
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
# 주제 표 — 위에서부터 먼저 걸리는 주제에 넣는다 (key, 이름, 낱말)
TOPICS = [
    ('agent',    'AI 에이전트·자동화',     r'에이전트|Agent|MCP|자동화|Automation|워크플로|workflow|브라우저 조작|컴퓨터 사용|Computer Use|Operator'),
    ('coding',   '바이브 코딩·개발 도구', r'바이브|Vibe|Claude Code|클로드 코드|Cursor|커서|Codex|코덱스|코딩|coding|IDE|CLI|프로그래밍|스킬|Skill'),
    ('image',    '이미지·영상·음성 생성',   r'이미지 생성|영상 생성|이미지|영상|비디오|video|Sora|소라|미드저니|Midjourney|나노바나나|Veo|Imagen|Diffusion|음성|voice|TTS|음악|music'),
    ('chatgpt',  '챗GPT·OpenAI',           r'챗GPT|ChatGPT|OpenAI|오픈AI|GPT-?\d|샘 올트먼|Altman'),
    ('claude',   '클로드·앤트로픽',         r'클로드|Claude|앤트로픽|Anthropic'),
    ('gemini',   '제미나이·구글',           r'제미나이|Gemini|구글|Google|NotebookLM|노트북LM|Gemma|젬마'),
    ('copilot',  '코파일럿·마이크로소프트', r'코파일럿|Copilot|마이크로소프트|Microsoft|MS\b'),
    ('search',   'AI 검색·퍼플렉시티',      r'퍼플렉시티|Perplexity|AI 검색|AI 모드|검색'),
    ('korea',    '국내 AI·네이버',          r'네이버|하이퍼클로바|소버린|카카오|LG AI|엑사원|EXAONE|삼성|SKT|KT\b|업스테이지|Upstage|솔라|국산'),
    ('edu',      '교육·학습',               r'교육|학습|학교|학생|교사|강의|수업|리터러시|literacy|튜터|tutor'),
    ('work',     '업무 활용·생산성',        r'업무|생산성|productivity|사무|문서|엑셀|Excel|보고서|회의|직장|기업 도입|워크스페이스|Workspace'),
    ('oss',      '오픈소스 모델·도구',      r'오픈소스|open[- ]?source|허깅페이스|Hugging ?Face|딥시크|DeepSeek|라마|Llama|미스트랄|Mistral|Qwen|큐원|GLM|로컬|local|오픈 모델|open[- ]weight'),
    ('other',    '그 밖의 AI 소식',         r'.'),
]
GH_DEFAULT_TOPIC = 'oss'   # GitHub 저장소는 다른 주제에 걸리지 않으면 "오픈소스 모델·도구"로

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
                    'source': clean(src.text if src is not None else ''), 'at': when(it.findtext('pubDate') or ''),
                    'desc': clean(it.findtext('description') or '')})
    return out

def og_desc(url):
    """기사 페이지의 og:description — 매체가 써 둔 요약문. 없으면 빈 문자열"""
    try:
        h = text(url)
        m = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)', h, re.I) or \
            re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']', h, re.I)
        return cut(m.group(1), 200) if m else ''
    except Exception:
        return ''

def translate(en):
    """영문 한 줄을 한국어로. DeepL 무료(키 있을 때) → MyMemory 무료(키 없을 때) → 실패하면 빈 문자열"""
    en = clean(en)[:300]
    if not en: return ''
    try:
        if DEEPL_KEY:
            body = urllib.parse.urlencode({'text': en, 'target_lang': 'KO', 'source_lang': 'EN'}).encode()
            r = urllib.request.urlopen(urllib.request.Request('https://api-free.deepl.com/v2/translate', data=body,
                                       headers={'Authorization': 'DeepL-Auth-Key ' + DEEPL_KEY}), timeout=30).read()
            return clean(json.loads(r)['translations'][0]['text'])
        r = json.loads(text('https://api.mymemory.translated.net/get?q=' + urllib.parse.quote(en) + '&langpair=en|ko'))
        t = r.get('responseData', {}).get('translatedText', '')
        return '' if not t or 'MYMEMORY WARNING' in t.upper() else clean(t)
    except Exception:
        return ''

items = []
def add(platform, title, url, source, note='', at=None, desc='', desc_en='', topic=None):
    items.append({'platform': platform, 'title': title, 'url': url, 'source': source, 'note': note,
                  'at': at.strftime('%Y-%m-%d') if at else '', 'desc': desc, 'desc_en': desc_en, 'topic': topic})

def ai_related(*texts):
    t = ' '.join(x for x in texts if x)
    return bool(re.search(AI_WORDS, t, re.I)) and not re.search(EXCLUDE, t, re.I)

# 1. 조코딩 IT뉴스 라이브 — 가장 최근 방송 1건 (제목 자체가 그 주 항목 목록이다)
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
            add('조코딩 IT뉴스 라이브 (유튜브)', title, f'https://www.youtube.com/watch?v={vid}', '조코딩', meta,
                desc='한 주의 AI·IT 소식을 라이브로 짚어 주는 방송. 제목의 항목이 그 주 다룬 주제다.', topic='other')
            return

# 2. GitHub 이번 주 인기 저장소 — 트렌딩(주간) 가운데 생성형 AI 활용에 걸리는 것 8개, 설명은 저장소 소개글을 번역
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
    rows.sort(key=lambda r: -r[0])
    n = 0
    for stars, name, desc, lang in rows:
        if not ai_related(name, desc): continue
        ko = translate(desc) if desc else ''
        add('GitHub 이번 주 인기 저장소', name, 'https://github.com/' + name, lang, f'{stars:,} stars (이번 주)',
            desc=ko or desc, desc_en=desc if ko else '', topic=None)
        n += 1
        if n >= 8: break

# 3. 긱뉴스(GeekNews) — 최근 7일 AI 관련 글을 포인트 순으로 8개, 요약은 글 본문 첫 부분(한국어)
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
            if at and at >= WEEK_AGO and ai_related(title):
                rows.append((int(pts.group(1)) if pts else 0, title, tid.group(1), at))
    rows.sort(key=lambda r: -r[0])
    for p, title, tid, at in rows[:8]:
        url = f'https://news.hada.io/topic?id={tid}'
        desc = ''
        try:
            m = re.search(r'id=["\']topic_contents["\'][^>]*>(.*?)</div>\s*<div', text(url), re.S)
            desc = cut(m.group(1), 220) if m else ''
        except Exception:
            pass
        add('긱뉴스(GeekNews) 화제 글', title, url, 'GeekNews', f'{p} points', at, desc=desc)

# 4. AI타임스 — 최근 7일 기사 중 활용 소식, 공개·출시·발표를 앞세워 8개, 요약은 기사 og:description
def aitimes():
    rows = [it for it in rss_items('https://www.aitimes.com/rss/allArticle.xml') if it['at'] and it['at'] >= WEEK_AGO and ai_related(it['title'], it['desc'])]
    rows.sort(key=lambda it: (0 if re.search(RELEASE, it['title']) else 1, -it['at'].timestamp()))
    for it in rows[:8]:
        add('AI타임스 주요 기사', it['title'], it['url'], 'AI타임스', '', it['at'], desc=it['desc'][:200] or og_desc(it['url']))

# 5. 플랫폼별 국내 보도 — 구글 뉴스 7일, 믿을 만한 매체만, 플랫폼당 2건 (구글 뉴스 본문은 없어 제목만)
def platforms():
    for plat, q in PLATFORMS:
        n = 0
        for it in rss_items('https://news.google.com/rss/search?q=' + urllib.parse.quote(q + ' when:7d') + '&hl=ko&gl=KR&ceid=KR:ko')[:15]:
            if not any(g in it['source'] for g in GOOD) or not ai_related(it['title']): continue
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

# 주제 배정 — 제목·설명으로 첫 번째 걸리는 주제. GitHub 저장소는 코딩·에이전트·이미지에 걸리지 않으면 오픈소스로
def assign(it):
    if it.get('topic'): return it['topic']
    t = ' '.join([it['title'], it.get('desc_en') or '', it.get('desc') or ''])
    for key, name, words in TOPICS:
        if key == 'other': break
        if re.search(words, t, re.I):
            if it['platform'].startswith('GitHub') and key not in ('coding', 'agent', 'image', 'oss'): continue
            return key
    return GH_DEFAULT_TOPIC if it['platform'].startswith('GitHub') else 'other'

def weight(it):
    m = re.search(r'([\d,]+)', it.get('note') or '')
    n = int(m.group(1).replace(',', '')) if m else 0
    return (1 if re.search(RELEASE, it['title']) else 0, n)

for it in week_items:
    it['topic'] = assign(it)
names = {k: n for k, n, _ in TOPICS}
groups = {}
for it in week_items:
    groups.setdefault(it['topic'], []).append(it)
for k in groups:
    groups[k].sort(key=lambda it: weight(it), reverse=True)
order = [k for k, _, _ in TOPICS]
topics = sorted(groups.keys(), key=lambda k: (-len(groups[k]), order.index(k)))
topics = [k for k in topics if k != 'other'][:9] + (['other'] if 'other' in groups else [])
topic_list = [{'key': k, 'name': names[k], 'count': len(groups[k]),
               'items': [{kk: vv for kk, vv in it.items() if kk != 'topic'} for it in groups[k]]} for k in topics]

# 게시글 제목 = 항목이 가장 많은 주제의 대표 소식(공개·출시가 있는 것 우선)
head = topic_list[0]['items'][0]['title'] if topic_list and topic_list[0]['items'] else '이번 주는 새 소식이 없습니다'
label = f'{TODAY.year}년 {TODAY.month}월 {(TODAY.day - 1) // 7 + 1}주'
post = {'date': TODAY.isoformat(), 'label': label, 'title': head, 'count': len(week_items), 'topics': topic_list,
        'items': [{kk: vv for kk, vv in it.items() if kk not in ('desc_en',)} for it in week_items]}
data = {'updated': TODAY.isoformat(), 'posts': []}
if os.path.exists(OUT):
    try: data = json.load(io.open(OUT, encoding='utf-8'))
    except Exception: pass
posts = [p for p in data.get('posts', []) if p.get('date') != post['date'] and p.get('label') != post['label']]   # 같은 주는 한 게시글만
posts.insert(0, post)
io.open(OUT, 'w', encoding='utf-8').write(json.dumps({'updated': TODAY.isoformat(), 'posts': posts[:26]}, ensure_ascii=False, indent=1))
print(label, post['count'], '건 →', head[:60])
for t in topic_list:
    print('  ', t['name'], t['count'])
