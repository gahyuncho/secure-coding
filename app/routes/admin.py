from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required

from app.extensions import db
from app.models import User, Product, Report
from app.utils import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    products = Product.query.order_by(Product.created_at.desc()).all()
    reports = Report.query.order_by(Report.created_at.desc()).limit(50).all()
    return render_template("admin.html", users=users, products=products, reports=reports)


@admin_bp.route("/users/<int:user_id>/toggle-suspend", methods=["POST"])
@login_required
@admin_required
def toggle_suspend_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    user.status = "suspended" if user.status == "active" else "active"
    db.session.commit()
    flash(f"{user.username} 계정 상태가 변경되었습니다.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/users/<int:user_id>/charge-balance", methods=["POST"])
@login_required
@admin_required
def charge_balance(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    try:
        amount = int(request.form.get("amount", "0"))
    except ValueError:
        amount = 0

    # 음수/과도한 값 방지 (테스트 편의 기능이므로 범위를 넓게 제한)
    if amount <= 0 or amount > 10_000_000:
        flash("유효하지 않은 충전 금액입니다.", "error")
        return redirect(url_for("admin.dashboard"))

    user.balance += amount
    db.session.commit()
    flash(f"{user.username}님에게 {amount}원을 충전했습니다.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/products/<int:product_id>/toggle-block", methods=["POST"])
@login_required
@admin_required
def toggle_block_product(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        abort(404)
    product.status = "blocked" if product.status == "active" else "active"
    db.session.commit()
    flash(f"상품 '{product.name}' 상태가 변경되었습니다.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        abort(404)
    db.session.delete(product)
    db.session.commit()
    flash("상품이 삭제되었습니다.", "success")
    return redirect(url_for("admin.dashboard"))
