import os
import random
import string

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, UploadFile, File
from fastapi.responses import Response as RawResponse
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas, config, nepal_geo
from ..database import get_db
from ..pdf_utils import build_receipt_pdf
from ..email_utils import send_order_confirmation, render_order_email_html, send_simple_email, render_return_email_html
from ..image_utils import save_image_to_db
from .cart import get_or_create_cart, SHIPPING_FEE

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _generate_order_number(db: Session) -> str:
    for _ in range(25):
        candidate = "BH-" + "".join(random.choices(string.digits, k=5))
        exists = db.query(models.Order).filter(models.Order.order_number == candidate).first()
        if not exists:
            return candidate
    raise HTTPException(status_code=500, detail="Could not allocate an order number, please retry")


def _order_to_schema(order: models.Order) -> schemas.OrderOut:
    return schemas.OrderOut(
        order_number=order.order_number, status=order.status,
        first_name=order.first_name, last_name=order.last_name, email=order.email,
        phone=order.phone, address=order.address, province=order.province, city=order.city, postal_code=order.postal_code,
        payment_method=order.payment_method, subtotal=order.subtotal,
        shipping_fee=order.shipping_fee, total=order.total, created_at=order.created_at,
        email_sent=order.email_sent,
        items=[
            schemas.OrderItemOut(
                product_title=i.product_title, color=i.color, color_hex=i.color_hex, size=i.size,
                unit_price=i.unit_price, quantity=i.quantity, line_total=i.unit_price * i.quantity,
            ) for i in order.items
        ],
    )


@router.post("", response_model=schemas.OrderOut)
async def create_order(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(...),
    address: str = Form(""),
    province: str = Form(""),
    city: str = Form(""),   # holds the District
    postal_code: str = Form(""),
    payment_method: str = Form(...),
    payment_reference: str = Form(""),
    payment_proof: UploadFile | None = File(None),
):
    if payment_method not in ("cod", "mobile_banking", "whatsapp"):
        raise HTTPException(status_code=400, detail="Invalid payment method")

    # WhatsApp orders are intentionally low-friction — just enough to identify and
    # reach the customer, with the rest coordinated over chat. Real checkout (COD /
    # mobile banking) still requires a real, validated Nepal shipping address.
    if payment_method != "whatsapp":
        if not nepal_geo.is_valid_district(province, city):
            raise HTTPException(status_code=400, detail="Please select a valid Nepal province and district — we currently only ship within Nepal.")
        if not nepal_geo.is_valid_postal_code(postal_code.strip()):
            raise HTTPException(status_code=400, detail="Postal code should be 5 digits (Nepal Post format), e.g. 44600 — or leave it blank.")
    else:
        address = address.strip() or "To be confirmed via WhatsApp"
        province = province.strip() or "To be confirmed"
        city = city.strip() or "To be confirmed"
        email = email.strip() or f"whatsapp-{phone.strip()}@bhura.local"

    cart = get_or_create_cart(request, response, db)
    if not cart.items:
        raise HTTPException(status_code=400, detail="Your cart is empty")

    # Size is chosen at checkout, not on the product page — so any item whose product
    # has managed variants (i.e. sizes actually exist to choose from) must have a size
    # set before an order can be placed. Products with no variants at all are unmanaged
    # and pass through with no size needed, same as before.
    missing_size_titles = []
    for item in cart.items:
        if item.size.strip():
            continue
        has_variants = db.query(models.ProductVariant).filter(
            models.ProductVariant.product_id == item.product_id
        ).first()
        if has_variants:
            missing_size_titles.append(item.product.title if item.product else "an item")
    if missing_size_titles:
        raise HTTPException(
            status_code=400,
            detail=f"Please select a size for: {', '.join(missing_size_titles)}.",
        )

    subtotal = sum(item.product.price * item.quantity for item in cart.items if item.product)
    if subtotal <= 0:
        raise HTTPException(status_code=400, detail="Your cart is empty")
    shipping_fee = SHIPPING_FEE
    total = subtotal + shipping_fee

    # Stock check BEFORE creating anything: a cart item only has a "managed" stock count
    # if a matching (product, size, color) variant row exists. Unmanaged items (e.g. a
    # quick-add with no size chosen) are let through as before. Any managed item that's
    # short on stock stops the whole order — nothing is written to the DB.
    shortfalls = []
    variants_to_decrement = []  # (variant, quantity) pairs, applied only after all checks pass
    for item in cart.items:
        if not item.product:
            continue
        variant = (
            db.query(models.ProductVariant)
            .filter(
                models.ProductVariant.product_id == item.product.id,
                models.ProductVariant.size == item.size,
                models.ProductVariant.color_name == item.color,
            )
            .first()
        )
        if variant is None:
            continue  # unmanaged stock — allow through
        if variant.stock_qty < item.quantity:
            label = f"{item.product.title} ({item.color} / {item.size})".strip()
            shortfalls.append(f"{label} — only {variant.stock_qty} left")
        else:
            variants_to_decrement.append((variant, item.quantity))

    if shortfalls:
        raise HTTPException(
            status_code=400,
            detail="Some items in your cart just went out of stock: " + "; ".join(shortfalls),
        )

    order_number = _generate_order_number(db)

    order = models.Order(
        order_number=order_number,
        first_name=first_name.strip(), last_name=last_name.strip(),
        email=email.strip(), phone=phone.strip(),
        address=address.strip(), province=province.strip(), city=city.strip(), postal_code=postal_code.strip(),
        payment_method=payment_method, payment_reference=payment_reference.strip(),
        status="pending", subtotal=subtotal, shipping_fee=shipping_fee, total=total,
    )
    db.add(order)
    db.flush()  # get order.id before adding items

    for item in cart.items:
        if not item.product:
            continue
        color_row = (
            db.query(models.ProductColor)
            .filter(models.ProductColor.product_id == item.product.id, models.ProductColor.name == item.color)
            .first()
        )
        db.add(models.OrderItem(
            order_id=order.id, product_id=item.product.id, product_title=item.product.title,
            color=item.color, color_hex=color_row.hex_code if color_row else "",
            size=item.size, unit_price=item.product.price, quantity=item.quantity,
        ))

    # Now that the order is guaranteed to be created, actually take the stock.
    for variant, qty in variants_to_decrement:
        variant.stock_qty -= qty

    if payment_proof is not None and payment_proof.filename:
        content = await payment_proof.read()
        order.payment_proof_path = save_image_to_db(db, content, payment_proof.content_type)

    # Clear the cart now that the order owns the items.
    for item in list(cart.items):
        db.delete(item)

    db.commit()
    db.refresh(order)

    # Build the receipt PDF fresh for the confirmation email. It is NOT persisted to
    # disk here — the download endpoint always regenerates from the order's current
    # state, so the receipt never goes stale after a status change (see the fix below).
    pdf_bytes = build_receipt_pdf(order)

    sent = send_order_confirmation(order.email, order_number, render_order_email_html(order), pdf_bytes)
    if sent:
        order.email_sent = True
        db.commit()
        db.refresh(order)

    return _order_to_schema(order)


def restore_stock_for_order(db: Session, order: models.Order) -> None:
    """Puts stock back for every managed item on an order — used when an order is cancelled."""
    for item in order.items:
        variant = (
            db.query(models.ProductVariant)
            .filter(
                models.ProductVariant.product_id == item.product_id,
                models.ProductVariant.size == item.size,
                models.ProductVariant.color_name == item.color,
            )
            .first()
        )
        if variant:
            variant.stock_qty += item.quantity


def take_stock_for_order(db: Session, order: models.Order) -> None:
    """Re-decrements stock — used if a cancelled order is reactivated. Never goes negative."""
    for item in order.items:
        variant = (
            db.query(models.ProductVariant)
            .filter(
                models.ProductVariant.product_id == item.product_id,
                models.ProductVariant.size == item.size,
                models.ProductVariant.color_name == item.color,
            )
            .first()
        )
        if variant:
            variant.stock_qty = max(0, variant.stock_qty - item.quantity)


CANCELLABLE_STATUSES = {"pending", "confirmed"}


def _normalize_phone(phone: str) -> str:
    """Compare only the last 10 digits so +977/977/leading-0 prefixes don't matter."""
    digits = "".join(ch for ch in phone if ch.isdigit())
    return digits[-10:] if len(digits) >= 10 else digits


def _order_contact_matches(order: models.Order, email: str = "", phone: str = "") -> bool:
    if email and order.email.strip().lower() == email.strip().lower():
        return True
    if phone and _normalize_phone(order.phone) == _normalize_phone(phone):
        return True
    return False


@router.post("/{order_number}/cancel", response_model=schemas.OrderOut)
def cancel_order(order_number: str, email: str = "", phone: str = "", db: Session = Depends(get_db)):
    order = (
        db.query(models.Order)
        .options(joinedload(models.Order.items))
        .filter(models.Order.order_number == order_number)
        .first()
    )
    if not order or not _order_contact_matches(order, email, phone):
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in CANCELLABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"This order is already '{order.status}' and can no longer be cancelled — contact us directly if you need help.",
        )

    order.status = "cancelled"
    restore_stock_for_order(db, order)
    db.commit()
    db.refresh(order)
    return _order_to_schema(order)


@router.get("/{order_number}", response_model=schemas.OrderOut)
def get_order(order_number: str, email: str = "", phone: str = "", db: Session = Depends(get_db)):
    order = (
        db.query(models.Order)
        .options(joinedload(models.Order.items))
        .filter(models.Order.order_number == order_number)
        .first()
    )
    if not order or not _order_contact_matches(order, email, phone):
        raise HTTPException(status_code=404, detail="Order not found")
    return _order_to_schema(order)


@router.get("/{order_number}/receipt.pdf")
def get_order_receipt(order_number: str, email: str = "", phone: str = "", db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.order_number == order_number).first()
    if not order or not _order_contact_matches(order, email, phone):
        raise HTTPException(status_code=404, detail="Order not found")

    # Always regenerate fresh from the order's current state — never cache to disk,
    # since a cached copy would freeze at whatever status existed on first download
    # and silently go stale after every later status change (confirmed/shipped/etc).
    pdf_bytes = build_receipt_pdf(order)
    return RawResponse(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="BHURA-Receipt-{order_number}.pdf"'},
    )


@router.post("/{order_number}/returns", response_model=schemas.ReturnRequestOut)
def request_return(order_number: str, payload: schemas.ReturnRequestIn, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.order_number == order_number).first()
    if not order or not _order_contact_matches(order, payload.email, payload.phone):
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "delivered":
        raise HTTPException(status_code=400, detail="Returns can only be requested for delivered orders.")
    existing = db.query(models.ReturnRequest).filter(models.ReturnRequest.order_id == order.id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"A return request already exists for this order (status: {existing.status}).")
    if not payload.reason.strip():
        raise HTTPException(status_code=400, detail="Please tell us the reason for the return.")

    ret = models.ReturnRequest(order_id=order.id, reason=payload.reason.strip(), status="requested")
    db.add(ret)
    db.commit()
    db.refresh(ret)

    send_simple_email(order.email, f"Return Requested — Order #{order.order_number}", render_return_email_html(order, ret))

    return schemas.ReturnRequestOut(
        id=ret.id, order_id=ret.order_id, order_number=order.order_number, reason=ret.reason,
        status=ret.status, admin_note=ret.admin_note, created_at=ret.created_at, updated_at=ret.updated_at,
    )


@router.get("/{order_number}/returns", response_model=schemas.ReturnRequestOut)
def get_return_status(order_number: str, email: str = "", phone: str = "", db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.order_number == order_number).first()
    if not order or not _order_contact_matches(order, email, phone):
        raise HTTPException(status_code=404, detail="Order not found")
    ret = db.query(models.ReturnRequest).filter(models.ReturnRequest.order_id == order.id).first()
    if not ret:
        raise HTTPException(status_code=404, detail="No return request exists for this order.")
    return schemas.ReturnRequestOut(
        id=ret.id, order_id=ret.order_id, order_number=order.order_number, reason=ret.reason,
        status=ret.status, admin_note=ret.admin_note, created_at=ret.created_at, updated_at=ret.updated_at,
    )
