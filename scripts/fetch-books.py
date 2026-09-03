# 교보문고 검색에서 윤성임 박사의 저서·공저 목록을 모아 books.json을 만든다 (표지·출판사·출간일·상세 주소)
import io, json, os, re, sys, html, datetime, urllib.parse, urllib.request

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36', 'Accept-Language': 'ko-KR,ko;q=0.9'}
ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT = os.path.join(ROOT, 'books.json')
AUTHOR = '윤성임'

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode('utf-8', 'ignore')

def unesc(t):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t or ''))).strip()

books = {}
for page in range(1, 15):
    url = f'https://search.kyobobook.co.kr/search?keyword={urllib.parse.quote(AUTHOR)}&target=total&gbCode=TOT&page={page}'
    try:
        h = get(url)
    except Exception as e:
        print('skip', url, e, file=sys.stderr); break
    blocks = h.split('class="prod_item"')[1:]
    if not blocks:
        break
    added = 0
    for b in blocks:
        author = re.search(r'prod_author_group(.*?)<!-- // 저자, 출판사 정보 -->', b, re.S)
        author_text = unesc(author.group(1)) if author else unesc(b[:3000])
        if AUTHOR not in author_text:
            continue
        pid = re.search(r'data-kbbfn-pid="([^"]+)"', b)
        title = re.search(r'data-kbbfn-title="([^"]*)"', b)
        bid = re.search(r'data-kbbfn-bid="([^"]+)"', b)
        pub = re.search(r'class="prod_publish">\s*<a[^>]*>([^<]+)</a>', b)
        date = re.search(r'class="date">([^<]+)</span>', b)
        if not (pid and title):
            continue
        d = date.group(1).strip() if date else ''
        m = re.search(r'(\d{4})년\s*(\d{2})월\s*(\d{2})일', d)
        iso = f'{m.group(1)}-{m.group(2)}-{m.group(3)}' if m else d
        books[pid.group(1)] = {
            'title': html.unescape(title.group(1)).strip(),
            'author': re.sub(r'\s*(저자|저|공저|글|지음|옮김)\s*', ' ', author_text).strip()[:80],
            'publisher': unesc(pub.group(1)) if pub else '',
            'date': iso,
            'cover': f'https://contents.kyobobook.co.kr/sih/fit-in/240x0/pdt/{bid.group(1)}.jpg' if bid else '',
            'url': f'https://product.kyobobook.co.kr/detail/{pid.group(1)}',
            'store': '교보문고',
        }
        added += 1
    if added == 0 and page > 1:
        break

# 종이책·전자책·큰글자책이 따로 잡히므로 같은 제목은 하나로 합친다 (가장 최근 판을 대표로, 판 수만 기록)
merged = {}
for b in sorted(books.values(), key=lambda x: x['date'], reverse=True):
    key = re.sub(r'\((큰글자[^)]*|[^)]*전자책[^)]*)\)|[^\w가-힣]', '', b['title'])
    if key in merged:
        merged[key]['editions'] += 1
    else:
        merged[key] = dict(b, editions=1)
items = list(merged.values())
io.open(OUT, 'w', encoding='utf-8').write(json.dumps({'updated': datetime.date.today().isoformat(), 'items': items}, ensure_ascii=False, indent=1))
print(len(items), 'books →', os.path.abspath(OUT))
for b in items[:6]:
    print(' ', b['date'], '|', b['title'][:40], '|', b['publisher'])
