import os
import tempfile

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

from app import create_app
from app.extensions import db as _db
from app.models import User


@pytest.fixture()
def app():
    db_fd, db_path = tempfile.mkstemp()

    flask_app = create_app(
        config_overrides={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "WTF_CSRF_ENABLED": False,  # CSRF 자체 검증은 test_tc07에서 별도의 app으로 확인
            "RATELIMIT_ENABLED": False,  # rate limit 상태가 테스트 세션 전체에 공유되어 오탐을 유발하므로 비활성화
        }
    )

    yield flask_app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture()
def client(app):
    return app.test_client()


def register_and_login(client, username, password="pw12345678", balance=None):
    client.post(
        "/register",
        data={"username": username, "password": password, "confirm": password},
        follow_redirects=True,
    )
    client.post("/login", data={"username": username, "password": password})
    if balance is not None:
        with client.application.app_context():
            u = User.query.filter_by(username=username).first()
            u.balance = balance
            _db.session.commit()
    return client
