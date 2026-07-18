from flask import Flask

from config import Config
from app.extensions import db, login_manager, csrf, socketio, limiter


def create_app(config_class=Config, config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(config_class)
    if config_overrides:
        # SQLAlchemy 엔진은 db.init_app() 이후 최초 접근 시점의 설정으로 바인딩되므로,
        # 테스트 등에서 DB URI를 바꾸려면 db.init_app()보다 먼저 적용해야 한다.
        app.config.update(config_overrides)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app)  # cors_allowed_origins 미지정 시 기본적으로 동일 출처만 허용됨.
    # 주의: cors_allowed_origins=[] 는 "모든 크로스오리진 차단"이 아니라 CORS 검사 자체를 비활성화하는
    # 설정이라 오히려 모든 출처를 허용하게 되므로 사용하지 말 것. 운영 배포 시 특정 도메인만 허용하려면
    # cors_allowed_origins=["https://your-domain.com"] 처럼 명시적으로 지정해야 함.
    limiter.init_app(app)

    from app.models import User
    from app import sockets  # noqa: F401  (SocketIO 이벤트 핸들러 등록을 위해 import)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.products import products_bp
    from app.routes.chat import chat_bp
    from app.routes.reports import reports_bp
    from app.routes.transfer import transfer_bp
    from app.routes.admin import admin_bp
    from app.routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(transfer_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()

    return app
