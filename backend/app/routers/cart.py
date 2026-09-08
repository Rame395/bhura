import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas, config
from ..database import get_db

router = APIRouter(prefix="/api/cart", tags=["cart"])

SHIPPING_FEE = 0  # Free shipping across Nepal, matching the storefront copy.


def get_or_create_cart(request: Request, response: Response, db: Session) -> models.Cart:
    token = request.cookies.get(config.CART_COOKIE_NAME)
    cart = None
    if token:
        cart = db.query(models.Cart).filter(models.Cart.token == token).first()
    if not cart:
        token = secrets.token_hex(24)
        cart = models.Cart(token=token)
        db.add(cart)
        db.commit()
        db.refresh(cart)
        response.set_cookie(
            key=config.CART_COOKIE_NAME, value=token,
            httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30,
        )
    return cart


def _serialize_cart(cart: models.Cart, db: Session) -> schemas.CartOut:
    items_out = []
    subtotal = 0
    for item in cart.items:
        product = item.product
        if not product:
            continue
        line_total = product.price * item.quantity
        subtotal += line_total
        primary_image = None
        if product.images:
            primary_image = sorted(product.images, key=lambda i: i.sort_order)[0].url

        max_stock = None
        variant = (
            db.query(models.ProductVariant)
            .filter(
                models.ProductVariant.product_id == product.id,
                models.ProductVariant.size == item.size,
                models.ProductVariant.color_name == item.color,
            )
            .first()
        )
        if variant:
            max_stock = variant.stock_qty

        color_row = (
            db.query(models.ProductColor)
            .filter(models.ProductColor.product_id == product.id, models.ProductColor.name == item.color)
            .first()
        )

        items_out.append(schemas.CartItemOut(
            id=item.id, product_id=product.id, slug=product.slug, title=product.title,
            color=item.color, color_hex=color_row.hex_code if color_row else None, size=item.size,
            quantity=item.quantity, unit_price=product.price, line_total=line_total, image=primary_image,
            max_stock=max_stock,
        ))
    total = subtotal + (SHIPPING_FEE if subtotal > 0 else 0)
    return schemas.CartOut(
        items=items_out, subtotal=subtotal, shipping_fee=SHIPPING_FEE if subtotal > 0 else 0,
        total=total, item_count=sum(i.quantity for i in items_out),
    )


@router.get("", response_model=schemas.CartOut)
def get_cart(request: Request, response: Response, db: Session = Depends(get_db)):
    cart = get_or_create_cart(request, response, db)
    return _serialize_cart(cart, db)


@router.post("/items", response_model=schemas.CartOut)
def add_item(payload: schemas.CartItemIn, request: Request, response: Response, db: Session = Depends(get_db)):
    cart = get_or_create_cart(request, response, db)

    product = db.query(models.Product).filter(
        models.Product.id == payload.product_id, models.Product.is_active == True  # noqa: E712
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if payload.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")

    existing = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.cart_id == cart.id,
            models.CartItem.product_id == product.id,
            models.CartItem.color == payload.color,
            models.CartItem.size == payload.size,
        )
        .first()
    )
    if existing:
        existing.quantity += payload.quantity
    else:
        db.add(models.CartItem(
            cart_id=cart.id, product_id=product.id,
            color=payload.color, size=payload.size, quantity=payload.quantity,
        ))
    db.commit()

    db.refresh(cart)
    return _serialize_cart(cart, db)


@router.patch("/items/{item_id}", response_model=schemas.CartOut)
def update_item(item_id: int, payload: schemas.CartItemUpdateIn, request: Request, response: Response, db: Session = Depends(get_db)):
    cart = get_or_create_cart(request, response, db)
    item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id, models.CartItem.cart_id == cart.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    if payload.quantity is not None:
        if payload.quantity < 1:
            db.delete(item)
            db.commit()
            db.refresh(cart)
            return _serialize_cart(cart, db)
        item.quantity = payload.quantity

    if payload.size is not None:
        size = payload.size.strip()
        if size:
            variant = db.query(models.ProductVariant).filter(
                models.ProductVariant.product_id == item.product_id,
                models.ProductVariant.color_name == item.color,
                models.ProductVariant.size == size,
            ).first()
            if not variant:
                raise HTTPException(status_code=400, detail=f"Size '{size}' isn't available for this item's color.")
            if variant.stock_qty <= 0:
                raise HTTPException(status_code=400, detail=f"Size '{size}' is currently out of stock in this color.")
        item.size = size

    db.commit()
    db.refresh(cart)
    return _serialize_cart(cart, db)


@router.delete("/items/{item_id}", response_model=schemas.CartOut)
def remove_item(item_id: int, request: Request, response: Response, db: Session = Depends(get_db)):
    cart = get_or_create_cart(request, response, db)
    item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id, models.CartItem.cart_id == cart.id
    ).first()
    if item:
        db.delete(item)
        db.commit()

    db.refresh(cart)
    return _serialize_cart(cart, db)
