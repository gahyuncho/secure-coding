from functools import wraps
from flask import abort
from flask_login import current_user


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            # 정보 노출 최소화를 위해 403만 반환 (권한 없음 사유 상세 노출 X)
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped


def active_required(view_func):
    """휴면(suspended) 계정은 로그인은 되어 있어도 주요 기능 차단."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if current_user.is_authenticated and current_user.is_suspended:
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped
