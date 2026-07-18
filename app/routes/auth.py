from flask import Blueprint, render_template, redirect, url_for, flash, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db, limiter
from app.forms import RegisterForm, LoginForm, MyPageForm
from app.models import User, Product

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("products.list_products"))

    form = RegisterForm()
    if form.validate_on_submit():
        # 아이디 중복 체크 (race condition은 DB unique 제약으로 최종 방어)
        if User.query.filter_by(username=form.username.data).first():
            flash("이미 사용 중인 아이디입니다.", "error")
            return render_template("register.html", form=form)

        user = User(username=form.username.data, balance=current_app.config["STARTING_BALANCE"])
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("회원가입이 완료되었습니다. 로그인해주세요.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")  # 무차별 대입 공격 방지
def login():
    if current_user.is_authenticated:
        return redirect(url_for("products.list_products"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        # 사용자 존재 여부를 노출하지 않도록 동일한 에러 메시지 사용
        if user is None or not user.check_password(form.password.data):
            flash("아이디 또는 비밀번호가 올바르지 않습니다.", "error")
            return render_template("login.html", form=form)

        if user.is_suspended:
            flash("휴면 처리된 계정입니다. 관리자에게 문의하세요.", "error")
            return render_template("login.html", form=form)

        login_user(user)
        flash("로그인되었습니다.", "success")
        return redirect(url_for("products.list_products"))

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("로그아웃되었습니다.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/mypage", methods=["GET", "POST"])
@login_required
def mypage():
    form = MyPageForm(bio=current_user.bio)
    if form.validate_on_submit():
        current_user.bio = form.bio.data
        if form.new_password.data:
            # 세션 탈취 등으로 인한 무단 비밀번호 변경 방지: 현재 비밀번호 확인 필수
            if not current_user.check_password(form.current_password.data):
                flash("현재 비밀번호가 올바르지 않습니다.", "error")
                return render_template("mypage.html", form=form, user=current_user)
            current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("저장되었습니다.", "success")
        return redirect(url_for("auth.mypage"))

    return render_template("mypage.html", form=form, user=current_user)


@auth_bp.route("/users/<username>")
@login_required
def view_user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    # 신고/휴면된 유저의 상세 정보는 최소한만 노출 (본인/관리자 제외)
    products = Product.query.filter_by(seller_id=user.id, status="active").order_by(
        Product.created_at.desc()
    ).all()
    return render_template("user_profile.html", profile_user=user, products=products)
