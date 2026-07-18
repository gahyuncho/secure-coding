from flask_login import current_user
from flask_socketio import join_room, emit, disconnect

from app.extensions import socketio, db
from app.models import Message, User


def _room_name(user_a_id: int, user_b_id: int) -> str:
    lo, hi = sorted([user_a_id, user_b_id])
    return f"dm-{lo}-{hi}"


@socketio.on("connect")
def handle_connect():
    # 로그인하지 않은 소켓 연결은 즉시 종료 (인증되지 않은 사용자 접근 차단)
    if not current_user.is_authenticated:
        disconnect()
        return
    join_room("global")


@socketio.on("send_global_message")
def handle_global_message(data):
    if not current_user.is_authenticated or current_user.is_suspended:
        return
    content = (data or {}).get("content", "").strip()
    if not content or len(content) > 1000:
        return

    message = Message(sender_id=current_user.id, receiver_id=None, content=content)
    db.session.add(message)
    db.session.commit()

    emit(
        "new_global_message",
        {"sender": current_user.username, "content": content, "timestamp": message.created_at.isoformat()},
        room="global",
    )


@socketio.on("join_dm")
def handle_join_dm(data):
    if not current_user.is_authenticated:
        return
    peer_username = (data or {}).get("peer_username", "")
    peer = User.query.filter_by(username=peer_username).first()
    if peer is None:
        return
    join_room(_room_name(current_user.id, peer.id))


@socketio.on("send_dm")
def handle_send_dm(data):
    if not current_user.is_authenticated or current_user.is_suspended:
        return
    peer_username = (data or {}).get("peer_username", "")
    content = (data or {}).get("content", "").strip()
    peer = User.query.filter_by(username=peer_username).first()
    if peer is None or not content or len(content) > 1000:
        return

    message = Message(sender_id=current_user.id, receiver_id=peer.id, content=content)
    db.session.add(message)
    db.session.commit()

    emit(
        "new_dm",
        {"sender": current_user.username, "content": content, "timestamp": message.created_at.isoformat()},
        room=_room_name(current_user.id, peer.id),
    )
