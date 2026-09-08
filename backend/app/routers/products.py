from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from .. import models, schemas, config, nepal_geo
from ..database import get_db
from ..settings_utils import get_setting

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/media/image/{image_id}")
def get_image(image_id: int, db: Session = Depends(get_db)):
    from fastapi import Response
    image = db.query(models.Image).filter(models.Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(
        content=image.data, media_type=image.content_type,
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.post("/subscribe", response_model=schemas.SubscriberOut)
def subscribe(payload: schemas.SubscriberIn, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    category = payload.category if payload.category in models.SUBSCRIBER_CATEGORIES else "all"

    existing = db.query(models.Subscriber).filter(models.Subscriber.email == email).first()
    if existing:
        existing.category = category  # resubscribing updates their stated interest
        db.commit()
        db.refresh(existing)
        return existing

    sub = models.Subscriber(email=email, category=category)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.get("/nepal-locations")
def get_nepal_locations():
    """Province -> District list, single source of truth shared with server-side validation."""
    return nepal_geo.NEPAL_PROVINCES


@router.get("/site-images/{slot}", response_model=list[schemas.SiteImageOut])
def get_active_site_images(slot: str, db: Session = Depends(get_db)):
    return (
        db.query(models.SiteImage)
        .filter(models.SiteImage.slot == slot, models.SiteImage.is_active == True)  # noqa: E712
        .order_by(models.SiteImage.sort_order)
        .all()
    )


@router.get("/settings", response_model=schemas.PublicSettingsOut)
def get_public_settings(db: Session = Depends(get_db)):
    """Storefront-facing settings: WhatsApp number, payment QR, which payment methods are on."""
    return schemas.PublicSettingsOut(
        whatsapp_number=get_setting(db, "whatsapp_number", config.WHATSAPP_DEFAULT),
        merchant_name=get_setting(db, "merchant_name", "BHURA APPAREL"),
        merchant_number=get_setting(db, "merchant_number", ""),
        qr_image_url=get_setting(db, "qr_image_path", "") or None,
        cod_enabled=get_setting(db, "cod_enabled", "true") == "true",
        mobile_banking_enabled=get_setting(db, "mobile_banking_enabled", "true") == "true",
        contact_phone=get_setting(db, "contact_phone", config.WHATSAPP_DEFAULT),
        instagram_url=get_setting(db, "instagram_url", ""),
        tiktok_url=get_setting(db, "tiktok_url", ""),
    )


def _card_from_product(p: models.Product) -> schemas.ProductCardOut:
    imgs = sorted(p.images, key=lambda i: i.sort_order)
    return schemas.ProductCardOut(
        id=p.id, slug=p.slug, title=p.title, price=p.price, compare_at_price=p.compare_at_price,
        department=p.department or "Clothing", subcategory=p.subcategory or "", category_slug=p.category.slug,
        is_new_arrival=p.is_new_arrival, collection_tag=p.collection_tag or "",
        primary_image=imgs[0].url if len(imgs) > 0 else None,
        secondary_image=imgs[1].url if len(imgs) > 1 else None,
    )


@router.get("/categories", response_model=list[schemas.CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    cats = db.query(models.Category).all()
    out = []
    for c in cats:
        count = db.query(func.count(models.Product.id)).filter(
            models.Product.category_id == c.id, models.Product.is_active == True  # noqa: E712
        ).scalar()
        out.append(schemas.CategoryOut(slug=c.slug, name=c.name, count=count))
    return out


@router.get("/products/taxonomy")
def get_taxonomy(category: str, db: Session = Depends(get_db)):
    """Department -> [subcategories] for the mega-menu, built live from whatever
    products actually exist — so a new department or subcategory just shows up,
    no code change needed. `category` is the gender slug (men/women)."""
    allowed_slugs = [category, "unisex"] if category in ("men", "women") else [category]
    rows = (
        db.query(models.Product.department, models.Product.subcategory)
        .join(models.Category)
        .filter(models.Category.slug.in_(allowed_slugs), models.Product.is_active == True)  # noqa: E712
        .distinct()
        .all()
    )
    taxonomy: dict[str, list[str]] = {}
    for department, subcategory in rows:
        department = department or "Clothing"
        if not subcategory:
            continue
        taxonomy.setdefault(department, [])
        if subcategory not in taxonomy[department]:
            taxonomy[department].append(subcategory)
    for department in taxonomy:
        taxonomy[department].sort()
    return taxonomy


@router.get("/products", response_model=list[schemas.ProductCardOut])
def list_products(
    category: Optional[str] = None,
    department: Optional[str] = None,
    subcategory: Optional[str] = None,
    is_new_arrival: Optional[bool] = None,
    on_sale: Optional[bool] = None,
    collection: Optional[str] = None,
    size: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    search: Optional[str] = None,
    sort: Optional[str] = Query(None, description="price_asc | price_desc | latest"),
    db: Session = Depends(get_db),
):
    q = (
        db.query(models.Product)
        .join(models.Category)
        .options(joinedload(models.Product.images), joinedload(models.Product.category))
        .filter(models.Product.is_active == True)  # noqa: E712
    )
    if category:
        allowed_slugs = [category, "unisex"] if category in ("men", "women") else [category]
        q = q.filter(models.Category.slug.in_(allowed_slugs))
    if department:
        q = q.filter(models.Product.department == department)
    if subcategory:
        q = q.filter(models.Product.subcategory == subcategory)
    if is_new_arrival is not None:
        q = q.filter(models.Product.is_new_arrival == is_new_arrival)
    if on_sale:
        q = q.filter(models.Product.compare_at_price.isnot(None), models.Product.compare_at_price > models.Product.price)
    if collection:
        q = q.filter(models.Product.collection_tag == collection)
    if min_price is not None:
        q = q.filter(models.Product.price >= min_price)
    if max_price is not None:
        q = q.filter(models.Product.price <= max_price)
    if size:
        q = q.join(models.ProductVariant).filter(models.ProductVariant.size == size)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(
            (models.Product.title.ilike(like))
            | (models.Product.subcategory.ilike(like))
            | (models.Product.department.ilike(like))
            | (models.Product.description.ilike(like))
        )

    if sort == "price_asc":
        q = q.order_by(models.Product.price.asc())
    elif sort == "price_desc":
        q = q.order_by(models.Product.price.desc())
    else:
        q = q.order_by(models.Product.created_at.desc())

    products = q.distinct().all()
    return [_card_from_product(p) for p in products]


@router.get("/products/{slug}", response_model=schemas.ProductDetailOut)
def get_product(slug: str, db: Session = Depends(get_db)):
    p = (
        db.query(models.Product)
        .options(
            joinedload(models.Product.images),
            joinedload(models.Product.colors),
            joinedload(models.Product.variants),
            joinedload(models.Product.category),
        )
        .filter(models.Product.slug == slug, models.Product.is_active == True)  # noqa: E712
        .first()
    )
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    visible_reviews = db.query(models.Review).filter(
        models.Review.product_id == p.id, models.Review.is_visible == True  # noqa: E712
    ).all()
    avg_rating = round(sum(r.rating for r in visible_reviews) / len(visible_reviews), 1) if visible_reviews else None
    return schemas.ProductDetailOut(
        id=p.id, slug=p.slug, title=p.title, price=p.price, compare_at_price=p.compare_at_price,
        description=p.description or "", material=p.material or "",
        department=p.department or "Clothing", subcategory=p.subcategory or "", category_slug=p.category.slug,
        collection_tag=p.collection_tag or "", is_new_arrival=p.is_new_arrival,
        images=[schemas.ImageOut.model_validate(i) for i in sorted(p.images, key=lambda i: i.sort_order)],
        colors=[schemas.ColorOut.model_validate(c) for c in p.colors],
        variants=[schemas.VariantOut.model_validate(v) for v in p.variants],
        avg_rating=avg_rating, review_count=len(visible_reviews),
    )


@router.get("/products/{slug}/reviews", response_model=list[schemas.ReviewOut])
def get_product_reviews(slug: str, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.slug == slug).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    reviews = (
        db.query(models.Review)
        .filter(models.Review.product_id == product.id, models.Review.is_visible == True)  # noqa: E712
        .order_by(models.Review.created_at.desc())
        .all()
    )
    return [schemas.ReviewOut.from_model(r) for r in reviews]


@router.post("/products/{slug}/reviews", response_model=schemas.ReviewOut)
def create_product_review(slug: str, payload: schemas.ReviewIn, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.slug == slug).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not (1 <= payload.rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    if not payload.customer_name.strip():
        raise HTTPException(status_code=400, detail="Please enter your name")

    # Verified Purchase: only if the given order number is real AND actually contains
    # this product — otherwise the review still goes through, just unverified.
    order_id = None
    if payload.order_number.strip():
        order = db.query(models.Order).filter(models.Order.order_number == payload.order_number.strip().upper()).first()
        if order and any(i.product_id == product.id for i in order.items):
            order_id = order.id

    review = models.Review(
        product_id=product.id, order_id=order_id, customer_name=payload.customer_name.strip(),
        rating=payload.rating, comment=payload.comment.strip(), is_visible=True,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return schemas.ReviewOut.from_model(review)
