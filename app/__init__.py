from flask import Flask

from config import Config
from app.extensions import db, login_manager, csrf, socketio, limiter


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app, cors_allowed_origins=[])  # 운영시 허용 origin 명시 필요
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
