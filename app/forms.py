from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange, Regexp, Optional, URL


class RegisterForm(FlaskForm):
    username = StringField(
        "아이디",
        validators=[
            DataRequired(),
            Length(min=3, max=32),
            Regexp(r"^[a-zA-Z0-9_]+$", message="아이디는 영문/숫자/밑줄만 가능합니다."),
        ],
    )
    password = PasswordField("비밀번호", validators=[DataRequired(), Length(min=8, max=128)])
    confirm = PasswordField(
        "비밀번호 확인", validators=[DataRequired(), EqualTo("password", message="비밀번호가 일치하지 않습니다.")]
    )
    submit = SubmitField("가입하기")


class LoginForm(FlaskForm):
    username = StringField("아이디", validators=[DataRequired(), Length(max=32)])
    password = PasswordField("비밀번호", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("로그인")


class MyPageForm(FlaskForm):
    bio = TextAreaField("소개글", validators=[Length(max=500)])
    current_password = PasswordField("현재 비밀번호 (비밀번호 변경 시에만 입력)", validators=[Length(min=0, max=128)])
    new_password = PasswordField("새 비밀번호 (변경 시에만 입력)", validators=[Length(min=0, max=128)])
    submit = SubmitField("저장")


class ProductForm(FlaskForm):
    name = StringField("상품명", validators=[DataRequired(), Length(max=100)])
    description = TextAreaField("상품 설명", validators=[Length(max=2000)])
    price = IntegerField("가격", validators=[DataRequired(), NumberRange(min=0, max=100_000_000)])
    image_url = StringField(
        "상품 사진 URL (선택)",
        validators=[Optional(), URL(require_tld=True, message="올바른 URL 형식이 아닙니다."), Length(max=500)],
    )
    submit = SubmitField("등록")


class ReportForm(FlaskForm):
    reason = TextAreaField("신고 사유", validators=[DataRequired(), Length(min=5, max=500)])
    submit = SubmitField("신고하기")


class TransferForm(FlaskForm):
    receiver_username = StringField("받는 사람 아이디", validators=[DataRequired(), Length(max=32)])
    amount = IntegerField("송금액", validators=[DataRequired(), NumberRange(min=1, max=100_000_000)])
    submit = SubmitField("송금")


class SearchForm(FlaskForm):
    q = StringField("검색어", validators=[Length(max=100)])
    submit = SubmitField("검색")
