import os
import secrets
import warnings

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

_env_secret_key = os.environ.get("SECRET_KEY")
if not _env_secret_key:
    # 공개 저장소에 고정된 기본값을 커밋해두면 세션/CSRF 토큰이 위조 가능해지므로,
    # 미설정 시 매 프로세스 시작마다 임의의 키를 생성한다 (재시작 시 기존 세션은 무효화됨).
    # 운영 배포에서는 반드시 SECRET_KEY를 환경변수로 고정 설정할 것.
    _env_secret_key = secrets.token_hex(32)
    warnings.warn(
        "SECRET_KEY 환경변수가 설정되지 않아 임시 키를 생성했습니다. "
        "재시작 시 모든 세션이 무효화됩니다. .env에 SECRET_KEY를 반드시 설정하세요.",
        RuntimeWarning,
    )


class Config:
    SECRET_KEY = _env_secret_key

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
