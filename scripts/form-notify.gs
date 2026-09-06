// 구글 폼 응답 알림 — 새 응답이 오면 텔레그램(박사님)에 요약을 보내고, 폼에 "이메일" 문항이 있고 채워졌을 때만 응답자에게 감사 메일을 보낸다.
// 로그인을 요구하지 않는 폼(이메일 주소 수집 = 수집 안 함)에서도 그대로 동작한다. 이메일 문항이 없으면 화면 감사 문구로 끝.
// 쓰는 법(폼마다 한 번, 약 3분): 폼 편집 화면 ⋮ → 스크립트 편집기 → 이 코드 붙여넣기 → 왼쪽 시계 아이콘(트리거)
//   → 트리거 추가 → 함수 onFormSubmit · 이벤트 소스 "양식에서" · 이벤트 유형 "양식 제출 시" → 저장 → 권한 허용(박사님 계정).
// 비밀값은 코드에 적지 않는다. 스크립트 편집기 왼쪽 톱니(프로젝트 설정) → 스크립트 속성에 TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID를 넣는다
// (오늘의 AI 소식 알림에 쓰는 봇과 같은 값을 써도 된다). 값이 없으면 텔레그램은 건너뛰고 메일만 보낸다.

const FORM_LABEL = '강사진 등록';            // 폼마다 바꾼다: '강사진 등록' / '개선 요청' / '강의 문의'
const EMAIL_QUESTION = '이메일';             // 응답자 이메일을 묻는 문항 제목의 앞부분(없으면 감사 메일은 건너뜀)
const THANKS_SUBJECT = '[소셜앤비즈] 등록 정보를 잘 받았습니다';
const THANKS_BODY =
  '안녕하세요, 소셜앤비즈 윤성임입니다.\n\n' +
  '보내 주신 정보를 잘 받았습니다. 함께해 주셔서 감사합니다.\n' +
  '내용을 정리한 뒤 다시 연락드리겠습니다. 수정·삭제는 언제든 이 메일로 답장해 주세요.\n\n' +
  '소셜앤비즈 윤성임 드림 · aceyun88@gmail.com · 010-2777-5004';

function onFormSubmit(e) {
  const rows = [];
  let respondentEmail = '';
  e.response.getItemResponses().forEach(function (r) {
    const q = r.getItem().getTitle();
    const a = String(r.getResponse());
    if (q.indexOf(EMAIL_QUESTION) === 0 && a.indexOf('@') > 0) respondentEmail = a.trim();
    if (a) rows.push(q.split('(')[0].trim() + ': ' + (a.length > 120 ? a.slice(0, 120) + '…' : a));
  });
  if (!respondentEmail && e.response.getRespondentEmail) respondentEmail = e.response.getRespondentEmail() || '';

  const text = '[' + FORM_LABEL + '] 새 응답 ' + Utilities.formatDate(new Date(), 'Asia/Seoul', 'MM-dd HH:mm') + '\n' + rows.join('\n');
  sendTelegram_(text);
  if (respondentEmail) MailApp.sendEmail({ to: respondentEmail, subject: THANKS_SUBJECT, body: THANKS_BODY, name: '소셜앤비즈 윤성임' });
}

function sendTelegram_(text) {
  const p = PropertiesService.getScriptProperties();
  const token = p.getProperty('TELEGRAM_BOT_TOKEN'), chat = p.getProperty('TELEGRAM_CHAT_ID');
  if (!token || !chat) return;
  UrlFetchApp.fetch('https://api.telegram.org/bot' + token + '/sendMessage', {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    payload: JSON.stringify({ chat_id: chat, text: text }),
  });
}
