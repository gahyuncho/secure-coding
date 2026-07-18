"""
보고서 5.2절의 TC-01~TC-08에 대응하는 자동화 테스트.
실행: python -m pytest tests/ -v
"""
import pytest

from app.extensions import db
from app.models import User, Product

from tests.conftest import register_and_login


def test_tc01_duplicate_username_rejected(client):
    """TC-01: 중복 아이디 회원가입 → 가입 거부 및 오류 메시지"""
    client.post("/register", data={"username": "dup", "password": "pw12345678", "confirm": "pw12345678"})
    resp = client.post(
        "/register",
        data={"username": "dup", "password": "pw12345678", "confirm": "pw12345678"},
        follow_redirects=True,
    )
    assert "이미 사용 중인 아이디" in resp.get_data(as_text=True)


def test_tc02_edit_others_product_forbidden(client, app):
    c1 = register_and_login(client, "owner1")
    with app.app_context():
        p = Product(name="타인상품", price=1000, seller_id=User.query.filter_by(username="owner1").first().id)
        db.session.add(p)
        db.session.commit()
        pid = p.id

    c2 = app.test_client()
    register_and_login(c2, "attacker1")
    resp = c2.post(f"/products/{pid}/edit", data={"name": "해킹", "description": "", "price": "1"})
    assert resp.status_code == 403


def test_tc03_javascript_scheme_image_url_rejected(client, app):
    register_and_login(client, "seller2")
    resp = client.post(
        "/products/new",
        data={"name": "상품", "description": "d", "price": "100", "image_url": "javascript:alert(1)"},
        follow_redirects=True,
    )
    with app.app_context():
        assert Product.query.filter_by(name="상품").first() is None
    assert resp.status_code == 200


def test_tc04_transfer_exceeding_balance_rejected(client, app):
    c1 = register_and_login(client, "poor1", balance=100)
    register_and_login(app.test_client(), "rich1")
    resp = c1.post(
        "/transfer/", data={"receiver_username": "rich1", "amount": "5000"}, follow_redirects=True
    )
    assert "잔액이 부족합니다" in resp.get_data(as_text=True)
    with app.app_context():
        assert User.query.filter_by(username="poor1").first().balance == 100


def test_tc05_buy_already_sold_product_rejected(client, app):
    seller = register_and_login(client, "seller3")
    with app.app_context():
        seller_id = User.query.filter_by(username="seller3").first().id
        p = Product(name="한정판", price=100, seller_id=seller_id)
        db.session.add(p)
        db.session.commit()
        pid = p.id

    buyer1 = app.test_client()
    register_and_login(buyer1, "buyer_a", balance=1000)
    buyer1.post(f"/products/{pid}/buy", follow_redirects=True)

    buyer2 = app.test_client()
    register_and_login(buyer2, "buyer_b", balance=1000)
    resp = buyer2.post(f"/products/{pid}/buy", follow_redirects=True)
    assert "이미 판매되었거나" in resp.get_data(as_text=True)


def test_tc06_non_admin_cannot_access_admin_page(client):
    register_and_login(client, "normaluser")
    resp = client.get("/admin/")
    assert resp.status_code == 403


def test_tc07_state_change_without_csrf_token_rejected():
    """TC-07: CSRF 토큰 없는 상태 변경 요청 → 요청 거부 (이 테스트만 CSRF를 실제로 활성화)"""
    import os
    import re
    import tempfile
    from app import create_app

    db_fd, db_path = tempfile.mkstemp()
    app = create_app(
        config_overrides={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "WTF_CSRF_ENABLED": True,
            "RATELIMIT_ENABLED": False,
        }
    )
    with app.app_context():
        u = User(username="csrftest")
        u.set_password("pw12345678")
        db.session.add(u)
        db.session.commit()
        user_id = u.id

    client = app.test_client()

    # 로그인 폼도 CSRF 보호 대상이므로, 로그인 페이지에서 실제 토큰을 추출해 정상적으로 로그인한다.
    login_page = client.get("/login").get_data(as_text=True)
    token_match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', login_page)
    assert token_match, "로그인 폼에서 csrf_token을 찾지 못함"
    csrf_token = token_match.group(1)

    login_resp = client.post(
        "/login",
        data={"username": "csrftest", "password": "pw12345678", "csrf_token": csrf_token},
    )
    assert login_resp.status_code == 302  # 로그인 성공 시 리다이렉트

    check = client.get("/mypage")
    assert check.status_code == 200  # 로그인이 실제로 적용됐는지 확인

    # 이후 상태 변경 요청에는 의도적으로 CSRF 토큰을 넣지 않고 전송
    resp = client.post("/mypage", data={"bio": "hacked", "current_password": "", "new_password": ""})
    assert resp.status_code == 400  # Flask-WTF는 토큰 누락/불일치 시 400 Bad Request 반환

    with app.app_context():
        assert db.session.get(User, user_id).bio != "hacked"

    os.close(db_fd)
    os.unlink(db_path)


def test_tc09_short_new_password_rejected(client, app):
    register_and_login(client, "shortpwuser")
    resp = client.post(
        "/mypage",
        data={"bio": "hi", "current_password": "pw12345678", "new_password": "x"},
        follow_redirects=True,
    )
    with app.app_context():
        u = User.query.filter_by(username="shortpwuser").first()
        assert u.check_password("pw12345678")  # 짧은 비밀번호로 바뀌지 않았어야 함
        assert not u.check_password("x")


def test_tc10_sold_product_cannot_be_edited(client, app):
    register_and_login(client, "soldseller")
    with app.app_context():
        seller_id = User.query.filter_by(username="soldseller").first().id
        p = Product(name="팔린상품", price=100, seller_id=seller_id, status="sold")
        db.session.add(p)
        db.session.commit()
        pid = p.id

    resp = client.post(
        f"/products/{pid}/edit",
        data={"name": "가격조작", "description": "", "price": "999999"},
        follow_redirects=True,
    )
    with app.app_context():
        assert db.session.get(Product, pid).name == "팔린상품"


def test_tc11_admin_cannot_toggle_sold_product(client, app):
    register_and_login(client, "soldseller2")
    with app.app_context():
        seller_id = User.query.filter_by(username="soldseller2").first().id
        p = Product(name="팔린상품2", price=100, seller_id=seller_id, status="sold")
        db.session.add(p)
        db.session.commit()
        pid = p.id
        admin = User(username="admin2", role="admin")
        admin.set_password("pw12345678")
        db.session.add(admin)
        db.session.commit()

    admin_client = app.test_client()
    admin_client.post("/login", data={"username": "admin2", "password": "pw12345678"})
    admin_client.post(f"/admin/products/{pid}/toggle-block", follow_redirects=True)

    with app.app_context():
        assert db.session.get(Product, pid).status == "sold"  # active로 되돌아가면 안 됨


def test_tc08_duplicate_report_rejected(client, app):
    seller = register_and_login(client, "seller4")
    with app.app_context():
        seller_id = User.query.filter_by(username="seller4").first().id
        p = Product(name="신고대상", price=100, seller_id=seller_id)
        db.session.add(p)
        db.session.commit()
        pid = p.id

    reporter = app.test_client()
    register_and_login(reporter, "reporter1")
    reporter.post(f"/report/product/{pid}", data={"reason": "첫 신고 사유입니다"}, follow_redirects=True)
    resp = reporter.post(
        f"/report/product/{pid}", data={"reason": "두 번째 신고 사유입니다"}, follow_redirects=True
    )
    assert "이미 신고한 대상입니다" in resp.get_data(as_text=True)
