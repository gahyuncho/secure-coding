import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # SECRET_KEY는 반드시 환경변수로 주입할 것. 기본값은 로컬 개발용 fallback.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 세션 쿠키 보안 설정
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # 배포 시 HTTPS 환경이면 True로 변경
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"

    # 신고 누적 임계값
    REPORT_THRESHOLD = 5

    # 테스트/데모 편의를 위한 회원가입 시 기본 지급 잔액
    STARTING_BALANCE = int(os.environ.get("STARTING_BALANCE", "10000"))

    WTF_CSRF_TIME_LIMIT = None
