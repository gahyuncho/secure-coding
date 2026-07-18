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
git clone https://github.com/<your-id>/secure-coding
cd secure-coding

# 2. 가상환경 생성 (miniconda 예시)
conda create -n secure-coding python=3.11 -y
conda activate secure-coding

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
# .env 파일에서 SECRET_KEY를 무작위 값으로 변경할 것

# 5. (최초 1회) 관리자 계정 생성
python seed_admin.py admin <admin-password>

# 6. 서버 실행
python run.py
```

서버 실행 후 http://127.0.0.1:5000 접속.

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
| 비밀번호 저장 | werkzeug `generate_password_hash` (pbkdf2:sha256), 평문 저장 금지 |
| 인증 | Flask-Login 세션 기반, HttpOnly/SameSite 쿠키, `session_protection="strong"` |
| 인가(IDOR) | 상품 수정/삭제 시 소유자 검증, 관리자 라우트는 `admin_required` 데코레이터로 role 체크 |
| SQL Injection | 전 구간 SQLAlchemy ORM 사용, raw query 미사용, 검색어도 파라미터 바인딩 |
| XSS | Jinja2 auto-escape 신뢰, 클라이언트 채팅 렌더링은 `innerText`/`textContent`만 사용해 `innerHTML` 삽입 금지 |
| CSRF | Flask-WTF CSRF 토큰 전체 폼/AJAX 요청에 적용 |
| 무차별 대입 공격 | 로그인/송금/신고 라우트에 Flask-Limiter로 rate limit 적용 |
| 송금 무결성 | 잔액 재조회 후 검증, DB 트랜잭션으로 원자적 처리 |
| 구매 무결성 | `SELECT ... FOR UPDATE`로 상품/잔액 재조회 후 검증, 이미 판매된 상품 재구매·본인 상품 구매 차단, 실패 시 rollback |
| 신고 남용 방지 | 동일 대상 중복 신고 차단, 자기 자신/자기 상품 신고 차단 |
| 정보 노출 | 로그인 실패 시 아이디 존재 여부를 구분하지 않는 동일 에러 메시지 |
| 실시간 채팅 인증 | 미인증 소켓 연결은 즉시 종료 (`disconnect()`) |

> 상세 보안 점검 항목 및 발견/수정 내역은 별도 보고서(PDF)에 기술.

## TODO / 남은 작업

- [ ] 실제 테스트 케이스 작성 및 체크리스트 점검
- [ ] 배포 시 `SESSION_COOKIE_SECURE=true`, HTTPS 적용
- [ ] SocketIO `cors_allowed_origins` 운영 도메인으로 제한
