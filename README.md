# Tiny Second-hand Shopping Platform

WHS 4기 Secure Coding 과제 — 간단한 중고거래 플랫폼 (Flask 기반)

## 기능

- 회원가입 / 로그인 / 마이페이지
- 상품 등록 / 조회 / 검색 / 수정 / 삭제
- **상품 구매** (잔액 차감/판매자 정산 + 판매완료 처리)
- 실시간 전체 채팅 및 1:1 채팅 (Flask-SocketIO)
- 유저/상품 신고 → 임계값 초과 시 자동 차단/휴면
- 유저 간 송금 (가상 포인트, 실제 결제 아님)
- 관리자 페이지 (유저/상품/신고 관리)

## 환경 설정 및 실행 방법 (WSL / Ubuntu 기준)

```bash
# 1. 저장소 클론
git clone https://github.com/gahyuncho/secure-coding
cd secure-coding

# 2. (최초 1회) python3-venv 설치가 안 되어 있다면
sudo apt update
sudo apt install python3.12-venv -y

# 3. 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 4. 의존성 설치
pip install -r requirements.txt

# 5. 환경변수 설정
cp .env.example .env
# .env 파일의 SECRET_KEY를 아래 명령어로 생성한 무작위 값으로 반드시 교체할 것
python3 -c "import secrets; print(secrets.token_hex(32))"

# 6. (최초 1회) 관리자 계정 생성 (아래는 예시 값입니다. 원하는 아이디/비밀번호로 바꿔서 실행하세요)
python seed_admin.py admin StrongPassword123!

# 7. 서버 실행
python run.py
```

서버 실행 후 http://127.0.0.1:5000 접속.

다음 실행부터는 3~4번(venv 생성, 설치) 없이 아래 두 줄이면 됩니다:
```bash
source venv/bin/activate
python run.py
```

> **주의**: Windows에서 WSL을 쓰는 경우, 프로젝트 폴더를 `/mnt/c/...`나 `/mnt/d/...` 같은 Windows 드라이브 경로가 아니라 **WSL 리눅스 홈 디렉토리(`~`) 안에 두고** 작업해야 합니다. Windows 드라이브 위에서는 `python3 -m venv`가 심볼릭 링크 문제로 정상 동작하지 않을 수 있습니다.

## 프로젝트 구조

```
secure-coding/
├── app/
│   ├── __init__.py       # 앱 팩토리
│   ├── extensions.py     # DB, 로그인, CSRF, SocketIO, Rate Limiter
│   ├── models.py         # User, Product, Report, Message, Transaction
│   ├── forms.py          # WTForms (서버측 입력 검증 + CSRF)
│   ├── sockets.py        # 실시간 채팅 이벤트 핸들러
│   ├── utils.py          # admin_required, active_required 데코레이터
│   ├── routes/           # 블루프린트 (auth, products, chat, reports, transfer, admin)
│   └── templates/
├── config.py
├── run.py
├── seed_admin.py
└── requirements.txt
```

## 적용된 보안 조치 (개발 중 지속 업데이트 예정)

| 항목 | 조치 |
|---|---|
| 비밀번호 저장 | werkzeug `generate_password_hash` 사용 (설치된 버전 기본 알고리즘 적용), 평문 저장 금지 |
| 인증 | Flask-Login 세션 기반, HttpOnly/SameSite 쿠키, `session_protection="strong"` |
| 인가(IDOR) | 상품 수정/삭제 시 소유자 검증, 관리자 라우트는 `admin_required` 데코레이터로 role 체크 |
| SQL Injection | 전 구간 SQLAlchemy ORM 사용, raw query 미사용, 검색어도 파라미터 바인딩 |
| XSS | Jinja2 auto-escape 신뢰, 클라이언트 채팅 렌더링은 `innerText`/`textContent`만 사용해 `innerHTML` 삽입 금지 |
| CSRF | Flask-WTF CSRF 토큰 전체 폼/AJAX 요청에 적용 |
| 무차별 대입 공격 | 로그인/회원가입/송금/신고/구매 라우트에 Flask-Limiter로 rate limit 적용 |
| 송금 무결성 | 송금자·수신자 양쪽 row lock(`with_for_update`)으로 잔액 재조회 후 검증, 트랜잭션으로 원자적 처리 (동시 요청으로 인한 이중 송금 방지) |
| 구매 무결성 | `SELECT ... FOR UPDATE`로 상품/잔액 재조회 후 검증, 이미 판매된 상품 재구매·본인 상품 구매 차단, 실패 시 rollback |
| 신고 남용 방지 | 동일 대상 중복 신고 차단, 자기 자신/자기 상품 신고 차단 |
| 정보 노출 | 로그인 실패 시 아이디 존재 여부를 구분하지 않는 동일 에러 메시지 |
| 실시간 채팅 인증 | 미인증 소켓 연결은 즉시 종료 (`disconnect()`) |
| 채팅 도배 방지 | 유저별 최소 전송 간격(0.5초) 제한 |
| 계정 탈취 대응 | 비밀번호 변경 시 현재 비밀번호 재확인 필수, 새 비밀번호도 회원가입과 동일하게 최소 8자 검증 |
| 이미지 URL XSS 방지 | `javascript:`/`data:` 등 위험 스킴 차단, http/https만 허용 |
| 회원가입 경쟁 조건 | 동시 가입 요청으로 인한 DB unique 제약 위반(IntegrityError)을 안전하게 처리 |
| SECRET_KEY 관리 | 소스코드에 고정 기본값을 두지 않고, 미설정 시 프로세스별 랜덤 키 생성 + 경고 (public 저장소 노출 대응) |
| 판매완료 상품 보호 | 판매완료(sold) 상품은 판매자가 수정할 수 없고, 관리자 차단 토글도 sold 상태는 건드리지 않도록 제외 |
| 로그아웃 상태 변경 | GET이 아닌 POST + CSRF 토큰 필요하도록 변경 (제3자 사이트에서 강제 로그아웃 유도 방지) |

> 상세 보안 점검 항목 및 발견/수정 내역은 별도 보고서(PDF)에 기술.

## 테스트

`tests/` 디렉토리에 pytest 기반 자동화 테스트 스위트가 있습니다. 실행 방법:

```bash
pip install pytest  # requirements.txt에 포함되어 있음
python -m pytest -q
```

회원가입 중복 방지, IDOR, XSS 이미지 URL 차단, 잔액 초과 송금 거부, 판매완료 상품 재구매 거부, 관리자 권한 검증, CSRF 검증, 중복 신고 방지 등 8개 시나리오를 검증합니다. 상세 내용은 보고서 5장 참고.

## 알려진 한계 (배포 시 반영 필요)

- 로컬 개발 환경 기준으로 작성되어 `SESSION_COOKIE_SECURE=false` 상태 — 실제 배포 시 HTTPS 환경에서 `true`로 변경 필요
- SocketIO는 `cors_allowed_origins`를 지정하지 않아 기본값(동일 출처만 허용)으로 동작 — 운영 도메인이 여러 개(예: 서브도메인)라면 명시적으로 설정 필요. **주의**: `cors_allowed_origins=[]`로 설정하면 반대로 CORS 검사 자체가 비활성화되어 모든 출처가 허용되므로 절대 사용하지 말 것 (초기 개발 중 이 실수를 했다가 발견하여 수정한 이력이 있음 — 보고서 6장 참고)
- Rate limit이 IP 기준이라 분산된 다중 IP 공격에는 완전한 방어가 아님 (계정 단위 잠금 미구현)
- 비밀번호 정책은 길이(8자 이상)만 검증, 복잡도 요구사항 없음
