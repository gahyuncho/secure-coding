import os
from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    # 배포 환경에서는 debug=False, 별도 WSGI/ASGI 서버 사용 권장
    socketio.run(app, host="127.0.0.1", port=5000, debug=debug)
