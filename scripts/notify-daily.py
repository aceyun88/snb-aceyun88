# 오늘의 AI 소식(ai-daily.json)을 텔레그램·이메일로 보낸다 — 비밀값은 GitHub Secrets에서만 읽고, 없는 통로는 조용히 건너뛴다 (추가 비용 없음: 텔레그램 봇 API·Gmail SMTP 모두 무료)
import io, json, os, smtplib, ssl, sys, urllib.parse, urllib.request
from email.mime.text import MIMEText
from email.header import Header

ROOT = os.path.join(os.path.dirname(__file__), '..')
SRC = os.path.join(ROOT, 'ai-daily.json')
SITE = 'https://snb-aceyun88.netlify.app/#today'

TG_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
TG_CHAT = os.environ.get('TELEGRAM_CHAT_ID', '').strip()
MAIL_USER = os.environ.get('GMAIL_USER', '').strip()          # 보내는 Gmail 주소
MAIL_PASS = os.environ.get('GMAIL_APP_PASSWORD', '').strip()  # Gmail 앱 비밀번호(16자리) — 계정 비밀번호가 아니다
MAIL_TO = os.environ.get('MAIL_TO', MAIL_USER).strip()         # 받는 주소(쉼표로 여러 명)

data = json.load(io.open(SRC, encoding='utf-8'))
day = (data.get('days') or [{}])[0]
items = day.get('items') or []
if not items:
    print('no items today'); sys.exit(0)

def line(i, it, md=False):
    t = it['title']
    src = ('공식 · ' if it.get('tier') == 1 else '') + it.get('source', '')
    if md:
        return f"{i}. <b>{t}</b>\n   {src} · <a href=\"{it['url']}\">원문</a>"
    return f"{i}. {t}\n   {src} · {it['url']}"

head = f"📢 오늘의 AI 소식 10 — {day.get('date')}\n공식 발표(OpenAI·Anthropic·Google) 우선 · 요금·기능은 발표 시점 기준\n"
foot = f"\n전체 보기: {SITE}\nⓒ 소셜앤비즈 윤성임 박사 · PK-PDCA 브릿지"
plain = head + '\n' + '\n'.join(line(i + 1, it) for i, it in enumerate(items)) + '\n' + foot
html_body = head.replace('\n', '<br>') + '<br>' + '<br>'.join(line(i + 1, it, md=True) for i, it in enumerate(items)) + '<br>' + foot.replace('\n', '<br>')

sent = []
# 1. 텔레그램 — 봇 토큰과 채팅 ID가 있을 때만. 메시지 4096자 제한이라 나눠 보낸다
if TG_TOKEN and TG_CHAT:
    chunks, cur = [], ''
    for para in html_body.split('<br>'):
        if len(cur) + len(para) > 3500:
            chunks.append(cur); cur = ''
        cur += para + '\n'
    chunks.append(cur)
    for c in chunks:
        body = urllib.parse.urlencode({'chat_id': TG_CHAT, 'text': c, 'parse_mode': 'HTML', 'disable_web_page_preview': 'true'}).encode()
        urllib.request.urlopen(urllib.request.Request(f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage', data=body), timeout=30).read()
    sent.append('telegram')

# 2. 이메일 — Gmail SMTP(앱 비밀번호)가 있을 때만
if MAIL_USER and MAIL_PASS and MAIL_TO:
    msg = MIMEText(html_body, 'html', 'utf-8')
    msg['Subject'] = Header(f"[오늘의 AI 소식] {day.get('date')} · {len(items)}건", 'utf-8')
    msg['From'] = MAIL_USER
    msg['To'] = MAIL_TO
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ssl.create_default_context()) as s:
        s.login(MAIL_USER, MAIL_PASS)
        s.sendmail(MAIL_USER, [a.strip() for a in MAIL_TO.split(',') if a.strip()], msg.as_string())
    sent.append('mail')

print('sent:', ', '.join(sent) or 'nothing (no secrets)')
