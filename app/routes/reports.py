from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user

from app.extensions import db, limiter
from app.forms import ReportForm
from app.models import Report, Product, User
from app.utils import active_required

reports_bp = Blueprint("reports", __name__, url_prefix="/report")


@reports_bp.route("/<target_type>/<int:target_id>", methods=["GET", "POST"])
@login_required
@active_required
@limiter.limit("20 per hour")  # 신고 남용/도배 방지
def create_report(target_type, target_id):
    if target_type not in ("user", "product"):
        abort(404)

    if target_type == "product":
        target = db.session.get(Product, target_id)
    else:
        target = db.session.get(User, target_id)
    if target is None:
        abort(404)

    # 자기 자신/자기 상품 신고 방지
    owner_id = target.id if target_type == "user" else target.seller_id
    if owner_id == current_user.id:
        flash("본인 또는 본인 상품은 신고할 수 없습니다.", "error")
        return redirect(url_for("products.list_products"))

    # 동일 대상 중복 신고 방지
    existing = Report.query.filter_by(
        reporter_id=current_user.id, target_type=target_type, target_id=target_id
    ).first()
    if existing:
        flash("이미 신고한 대상입니다.", "error")
        return redirect(url_for("products.list_products"))

    form = ReportForm()
    if form.validate_on_submit():
        report = Report(
            reporter_id=current_user.id,
            target_type=target_type,
            target_id=target_id,
            reason=form.reason.data,
        )
        db.session.add(report)

        threshold = current_app.config["REPORT_THRESHOLD"]
        if target_type == "product":
            target.report_count += 1
            # active 상태인 상품만 차단 대상으로 함 — 이미 판매완료(sold)된 상품이
            # 신고 누적만으로 blocked 처리되어 구매자가 상세페이지에 접근 못하게 되는 문제 방지
            if target.report_count >= threshold and target.status == "active":
                target.status = "blocked"
        else:
            target.report_count += 1
            if target.report_count >= threshold and target.status == "active":
                target.status = "suspended"

        db.session.commit()
        flash("신고가 접수되었습니다.", "success")
        return redirect(url_for("products.list_products"))

    return render_template("report_form.html", form=form, target_type=target_type, target_id=target_id)
