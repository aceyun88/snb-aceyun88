# 기사(파이낸스투데이) 본문에서 출강·협업 기관명을 뽑아 clients.json 후보 목록을 만든다 — 최종 게시 여부는 사람이 확인한다
import io, json, os, re, sys, html, urllib.request
from collections import Counter, defaultdict

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36', 'Accept-Language': 'ko-KR,ko;q=0.9'}
ROOT = os.path.join(os.path.dirname(__file__), '..')
NEWS = os.path.join(ROOT, 'news.json')
OUT = os.path.join(ROOT, 'clients.json')

# 기관명으로 끝나는 꼬리말 — 이 꼬리말로 끝나는 한글 낱말 묶음을 기관명 후보로 본다
TAIL = r'(?:청|처|부|원|협회|공단|공사|공제회|대학교|대학|대학원|학회|재단|센터|진흥원|연구원|연구소|상공회의소|조합|은행|그룹|산업단지|기술원|교육원|교육청|시청|군청|구청|시|군|평생학습관|도서관|복지관|여성회관|창업지원단|테크노파크|사회적경제지원센터|농업기술센터)'
CAND = re.compile(r'(?<![가-힣A-Za-z])([가-힣A-Za-z0-9·]{2,14}' + TAIL + r')(?![가-힣])')
# 기관이 아닌데 꼬리말이 같은 흔한 낱말
STOP = {'소셜앤비즈', '한국AI융합비즈연구소', '파이낸스투데이', '한국AI융합비즈연구소원', '연구원', '대학교', '협회', '센터', '진흥원', '조합', '은행', '그룹', '재단', '학회', '공단', '공사',
        '이시', '당시', '동시', '역시', '도시', '표시', '제시', '전시', '암시', '지시', '개시', '시시', '다시', '혹시', '잠시', '즉시', '수시', '상시', '한시', '일시', '거의시',
        '군', '시', '부', '처', '청', '원', '기업부', '본부', '외부', '내부', '일부', '전부', '대부', '상부', '학부', '남부', '북부', '중부', '동부', '서부', '정부', '중앙정부', '지방정부',
        '정기후원', '국민은행', '연락처', '올인원', '입학지원센터', '퍼블리시', '플래시', '퍼머컬처', '기술지원', 'AI융합비즈연구소', '스마트농수산학부', '학부', '지원센터', '고객지원센터', 'AI연구소', '디지털리터러시', '주산학원', '코칭연구소', '경영연구소', '교육연구소', '창업연구소', 'AI리터러시', '리터러시', '반드시', '전문위원', '임직원', '선임연구원', '연구위원', '수석연구원', '책임연구원', '아키텍처', '윤성임AI리터러시', '여성대학', '주부대학', '교육지원청', '농업기술센터', '지역사회', '공공기관', '지방자치단체', '대기업', '중소기업', '스타트업', '벤처기업', '사회적기업', '마을기업', '협동조합', '평생교육원', '학회', '연구소', '기술원', '교육원',
        '구', '친구', '요구', '연구', '도구', '입구', '출구', '지구', '가구', '기구', '문구', '추구', '탐구', '강구', '연구원', '심층연구', '고객센터', '콜센터', '데이터센터', '물류센터'}

# 같은 기관의 다른 표기는 하나로
ALIAS = {'목포대학교': '국립목포대학교', '청송농업기술센터': '청송군농업기술센터', '영덕농업기술센터': '영덕군농업기술센터'}

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode('utf-8', 'ignore')

def body_text(h):
    m = re.search(r'<article[^>]*id="article-view-content-div"[^>]*>(.*?)</article>', h, re.S) or re.search(r'id="article-view-content-div"[^>]*>(.*?)<div class="(?:article-footer|writer)', h, re.S)
    t = m.group(1) if m else h
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t)))

news = json.load(io.open(NEWS, encoding='utf-8'))['items']
prev = {}
if os.path.exists(OUT):
    try:
        for c in json.load(io.open(OUT, encoding='utf-8')).get('items', []): prev[c['name']] = c
    except Exception: pass

count, first, sample = Counter(), {}, defaultdict(list)
n = 0
for it in news:
    text = it['title']
    if it.get('source') == '파이낸스투데이' and n < 120:
        try:
            text += ' ' + body_text(get(it['url'])); n += 1
        except Exception as e:
            print('skip', it['url'], repr(e)[:60], file=sys.stderr)
    for m in CAND.finditer(text):
      for name in m.group(1).split('·'):   # "국립목포대학교·동국대학교"처럼 붙은 것은 나눈다
        name = ALIAS.get(name.strip(), name.strip())
        if not re.search(TAIL + '$', name) or name in STOP or len(name) < 3 or '소셜앤비즈' in name or '윤성임' in name: continue
        count[name] += 1
        if name not in first or it['date'] > first[name]: first[name] = it['date']
        if len(sample[name]) < 2 and it['url'] not in sample[name]: sample[name].append(it['url'])

items = []
for name, c in count.most_common():
    old = prev.get(name, {})
    items.append({'name': name, 'count': c, 'latest': first[name], 'articles': sample[name],
                  'logo': old.get('logo', ''), 'show': old.get('show', c >= 3)})
io.open(OUT, 'w', encoding='utf-8').write(json.dumps({'updated': __import__('datetime').date.today().isoformat(),
    '_안내': '기사 본문에서 자동으로 뽑은 기관명 후보. show가 true인 것만 홈페이지에 나온다(처음 값은 3회 이상 언급). 사람이 검토해 show를 고치고, 로고 파일이 있으면 clients/영문이름.png 를 logo에 적는다. 이름·show·logo는 다음 수집 때도 보존된다.',
    'items': items}, ensure_ascii=False, indent=1))
print(len(items), '기관 후보 →', OUT, '(본문 읽은 기사', n, '건)')
for x in items[:40]: print(' ', x['count'], x['name'], '' if x['show'] else '(숨김)')
