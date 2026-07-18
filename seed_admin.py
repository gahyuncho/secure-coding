"""최초 관리자 계정을 생성하는 1회성 스크립트.
사용법: python seed_admin.py <username> <password>
"""
import sys
from app import create_app
from app.extensions import db
from app.models import User

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("사용법: python seed_admin.py <username> <password>")
        sys.exit(1)

    username, password = sys.argv[1], sys.argv[2]
    app = create_app()
    with app.app_context():
        if User.query.filter_by(username=username).first():
            print("이미 존재하는 아이디입니다.")
            sys.exit(1)

        admin = User(username=username, role="admin")
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"관리자 계정 '{username}' 생성 완료.")
