from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db, limiter
from app.forms import ProductForm, SearchForm
from app.models import Product, User, Transaction
from app.utils import active_required

products_bp = Blueprint("products", __name__, url_prefix="/products")


@products_bp.route("/")
def list_products():
    search_form = SearchForm(request.args, meta={"csrf": False})
    query = Product.query.filter_by(status="active")

    q = request.args.get("q", "").strip()
    if q:
        # ORM의 파라미터 바인딩을 사용하므로 SQL Injection에 안전함 (raw query 사용 금지)
        like_pattern = f"%{q}%"
        query = query.filter(Product.name.ilike(like_pattern))

    products = query.order_by(Product.created_at.desc()).all()
    return render_template("products.html", products=products, search_form=search_form, q=q)


@products_bp.route("/mine")
@login_required
def my_products():
    products = Product.query.filter_by(seller_id=current_user.id).order_by(Product.created_at.desc()).all()
    return render_template("my_products.html", products=products)


@products_bp.route("/purchased")
@login_required
def purchased_products():
    products = (
        Product.query.filter_by(buyer_id=current_user.id)
        .order_by(Product.created_at.desc())
        .all()
    )
    return render_template("purchased_products.html", products=products)


@products_bp.route("/new", methods=["GET", "POST"])
@login_required
@active_required
def new_product():
    form = ProductForm()
    if form.validate_on_submit():
        image_url = form.image_url.data.strip()
        # javascript:, data: 등 위험한 스킴을 통한 XSS 방지 - http/https만 허용
        if image_url and not image_url.lower().startswith(("http://", "https://")):
            flash("이미지 URL은 http:// 또는 https://로 시작해야 합니다.", "error")
            return render_template("product_form.html", form=form, mode="new")

        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image_url=image_url,
            seller_id=current_user.id,
        )
        db.session.add(product)
        db.session.commit()
        flash("상품이 등록되었습니다.", "success")
        return redirect(url_for("products.product_detail", product_id=product.id))

    return render_template("product_form.html", form=form, mode="new")


@products_bp.route("/<int:product_id>")
def product_detail(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        abort(404)
    # 관리자에 의해 차단된 상품만 소유자/관리자에게 비공개. 판매완료(sold)는 누구나 조회 가능.
    if product.status == "blocked":
        if not current_user.is_authenticated or (
            current_user.id != product.seller_id and not current_user.is_admin
        ):
            abort(404)
    return render_template("product_detail.html", product=product)


@products_bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
@active_required
def edit_product(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        abort(404)
    # 소유자 검증: 다른 사람 상품을 수정할 수 없도록 함 (IDOR 방지)
    if product.seller_id != current_user.id:
        abort(403)

    form = ProductForm(obj=product)
    if form.validate_on_submit():
        image_url = form.image_url.data.strip()
        if image_url and not image_url.lower().startswith(("http://", "https://")):
            flash("이미지 URL은 http:// 또는 https://로 시작해야 합니다.", "error")
            return render_template("product_form.html", form=form, mode="edit")

        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.image_url = image_url
        db.session.commit()
        flash("수정되었습니다.", "success")
        return redirect(url_for("products.product_detail", product_id=product.id))

    return render_template("product_form.html", form=form, mode="edit")


@products_bp.route("/<int:product_id>/buy", methods=["POST"])
@login_required
@active_required
@limiter.limit("10 per minute")
def buy_product(product_id):
    # 동시 구매 요청 경합 방지를 위해 row lock을 걸고 최신 상태를 다시 읽음
    product = db.session.query(Product).filter_by(id=product_id).with_for_update().first()
    if product is None:
        abort(404)

    if product.status != "active":
        flash("이미 판매되었거나 구매할 수 없는 상품입니다.", "error")
        return redirect(url_for("products.product_detail", product_id=product_id))

    if product.seller_id == current_user.id:
        flash("본인 상품은 구매할 수 없습니다.", "error")
        return redirect(url_for("products.product_detail", product_id=product_id))

    buyer = db.session.query(User).filter_by(id=current_user.id).with_for_update().first()
    seller = db.session.get(User, product.seller_id)

    if buyer.balance < product.price:
        flash("잔액이 부족합니다. 마이페이지/송금에서 잔액을 확인해주세요.", "error")
        return redirect(url_for("products.product_detail", product_id=product_id))

    try:
        buyer.balance -= product.price
        seller.balance += product.price
        product.status = "sold"
        product.buyer_id = buyer.id
        db.session.add(
            Transaction(sender_id=buyer.id, receiver_id=seller.id, amount=product.price)
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("구매 처리 중 오류가 발생했습니다.", "error")
        return redirect(url_for("products.product_detail", product_id=product_id))

    flash(f"'{product.name}' 구매가 완료되었습니다.", "success")
    return redirect(url_for("products.product_detail", product_id=product_id))


@products_bp.route("/<int:product_id>/delete", methods=["POST"])
@login_required
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        abort(404)
    if product.seller_id != current_user.id and not current_user.is_admin:
        abort(403)

    db.session.delete(product)
    db.session.commit()
    flash("삭제되었습니다.", "success")
    return redirect(url_for("products.my_products"))
