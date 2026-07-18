from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db, limiter
from app.forms import TransferForm
from app.models import User, Transaction
from app.utils import active_required

transfer_bp = Blueprint("transfer", __name__, url_prefix="/transfer")


@transfer_bp.route("/", methods=["GET", "POST"])
@login_required
@active_required
@limiter.limit("10 per minute")
def transfer():
    form = TransferForm()
    if form.validate_on_submit():
        receiver = User.query.filter_by(username=form.receiver_username.data).first()
        amount = form.amount.data

        if receiver is None:
            flash("받는 사람을 찾을 수 없습니다.", "error")
            return render_template("transfer.html", form=form)

        if receiver.id == current_user.id:
            flash("본인에게는 송금할 수 없습니다.", "error")
            return render_template("transfer.html", form=form)

        # DB 레벨에서 한 번 더 최신 잔액을 조회하여 race condition에 의한 이중 송금 최소화
        sender = db.session.get(User, current_user.id)
        if sender.balance < amount:
            flash("잔액이 부족합니다.", "error")
            return render_template("transfer.html", form=form)

        try:
            sender.balance -= amount
            receiver.balance += amount
            db.session.add(Transaction(sender_id=sender.id, receiver_id=receiver.id, amount=amount))
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("송금 처리 중 오류가 발생했습니다.", "error")
            return render_template("transfer.html", form=form)

        flash(f"{receiver.username}님에게 {amount}원을 송금했습니다.", "success")
        return redirect(url_for("transfer.transfer"))

    history = (
        Transaction.query.filter(
            (Transaction.sender_id == current_user.id) | (Transaction.receiver_id == current_user.id)
        )
        .order_by(Transaction.created_at.desc())
        .limit(20)
        .all()
    )
    return render_template("transfer.html", form=form, history=history)
