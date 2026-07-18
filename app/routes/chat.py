from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

from app.models import Message, User
from app.utils import active_required

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.route("/")
@login_required
@active_required
def global_chat():
    history = Message.query.filter_by(receiver_id=None).order_by(Message.created_at.desc()).limit(50).all()
    history.reverse()
    return render_template("chat_global.html", history=history)


@chat_bp.route("/<username>")
@login_required
@active_required
def direct_chat(username):
    peer = User.query.filter_by(username=username).first()
    if peer is None:
        abort(404)
    if peer.id == current_user.id:
        abort(400)

    history = (
        Message.query.filter(
            (
                (Message.sender_id == current_user.id) & (Message.receiver_id == peer.id)
            )
            | (
                (Message.sender_id == peer.id) & (Message.receiver_id == current_user.id)
            )
        )
        .order_by(Message.created_at.asc())
        .limit(100)
        .all()
    )
    return render_template("chat_direct.html", history=history, peer=peer)
