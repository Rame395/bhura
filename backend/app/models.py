from sqlalchemy import (
    Column, Integer, String, Boolean, Text, ForeignKey, DateTime, Date, UniqueConstraint, LargeBinary
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    slug = Column(String(50), unique=True, nullable=False)   # "men" / "women"
    name = Column(String(50), nullable=False)                # "Men" / "Women"

    products = relationship("Product", back_populates="category")


class Department(Base):
    """Admin-manageable Category/Department values (Clothing, Shoes, Accessories,
    Sports, ...). Kept as a lookup table for validation + populating dropdowns —
    Product.department stays a plain string column, so this needs no migration."""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    slug = Column(String(50), unique=True, nullable=False)   # "shoes"
    name = Column(String(50), nullable=False)                # "Shoes"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    slug = Column(String(140), unique=True, nullable=False, index=True)
    title = Column(String(120), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)  # this is GENDER (men/women)
    department = Column(String(30), default="Clothing")   # Shoes | Clothing | Accessories | Sports — the Puma-style "Category"
    subcategory = Column(String(60), default="")             # Outerwear, Essentials, Bottoms, Knitwear...
    price = Column(Integer, nullable=False)                  # NPR, whole rupees — the current selling price
    compare_at_price = Column(Integer, nullable=True)        # optional "was" price; sale is shown when this > price
    description = Column(Text, default="")
    material = Column(String(200), default="")
    collection_tag = Column(String(60), default="")          # e.g. "drop-01-monolith", nullable-ish
    is_new_arrival = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    category = relationship("Category", back_populates="products")
    images = relationship(
        "ProductImage", back_populates="product",
        cascade="all, delete-orphan", order_by="ProductImage.sort_order"
    )
    colors = relationship("ProductColor", back_populates="product", cascade="all, delete-orphan")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    url = Column(String(500), nullable=False)
    sort_order = Column(Integer, default=0)
    color_name = Column(String(50), nullable=True)   # optional — ties a photo to one color's swatch

    product = relationship("Product", back_populates="images")


class ProductColor(Base):
    __tablename__ = "product_colors"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name = Column(String(50), nullable=False)
    hex_code = Column(String(7), default="#111111")

    product = relationship("Product", back_populates="colors")


class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (UniqueConstraint("product_id", "size", "color_name", name="uix_variant"),)

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    size = Column(String(10), nullable=False)          # S, M, L, XL, XXL
    color_name = Column(String(50), default="")
    stock_qty = Column(Integer, default=0)

    product = relationship("Product", back_populates="variants")


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    color = Column(String(50), default="")
    size = Column(String(10), default="")
    quantity = Column(Integer, default=1)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    order_number = Column(String(20), unique=True, nullable=False, index=True)

    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    email = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(String(300), nullable=False)
    city = Column(String(80), nullable=False)          # holds the District (Nepal admin structure)
    province = Column(String(50), nullable=False, default="")
    postal_code = Column(String(20), default="")

    payment_method = Column(String(20), nullable=False)      # cod | mobile_banking
    payment_reference = Column(String(200), default="")
    payment_proof_path = Column(String(300), default="")

    status = Column(String(20), default="pending")           # pending|confirmed|shipped|delivered|cancelled
    subtotal = Column(Integer, nullable=False)
    shipping_fee = Column(Integer, default=0)
    total = Column(Integer, nullable=False)

    email_sent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"))
    product_title = Column(String(120), nullable=False)
    color = Column(String(50), default="")
    color_hex = Column(String(7), default="")
    size = Column(String(10), default="")
    unit_price = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)


class AdminSession(Base):
    __tablename__ = "admin_sessions"

    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)


class SiteSetting(Base):
    __tablename__ = "site_settings"

    key = Column(String(50), primary_key=True)
    value = Column(Text, default="")


class Expense(Base):
    """
    Manually-logged business expenses (rent, wages, inventory purchases, etc).
    Income is NOT a mirrored table here — it's derived live from Order totals
    (excluding cancelled orders), since that data already exists and shouldn't
    be duplicated/kept in sync by hand. is_recurring is a plain label for the
    admin's own reference — it does not auto-generate future entries.
    """
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)
    category = Column(String(30), nullable=False)
    amount = Column(Integer, nullable=False)          # NPR
    note = Column(String(300), default="")
    expense_date = Column(Date, nullable=False)
    is_recurring = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Review(Base):
    """Customer product reviews. order_id links a review to the specific order that
    contained the product, so we can mark it 'Verified Purchase' — nullable because
    we still allow a review without one rather than blocking feedback entirely."""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    customer_name = Column(String(100), nullable=False)
    rating = Column(Integer, nullable=False)   # 1-5
    comment = Column(Text, default="")
    is_visible = Column(Boolean, default=True)   # admin can hide without deleting
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product")


RETURN_STATUSES = ["requested", "approved", "rejected", "received", "refunded"]


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(20), default="requested")
    admin_note = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    order = relationship("Order")


SITE_IMAGE_SLOTS = {
    # slot key: (display label, "single" one active image | "multi" any number, page)
    "homepage_hero": ("Homepage — Hero Banner (rotates)", "multi", "index.html"),
    "homepage_story": ("Homepage — Editorial Story Section", "single", "index.html"),
    "homepage_tile_men": ("Homepage — Men Tile", "single", "index.html"),
    "homepage_tile_women": ("Homepage — Women Tile", "single", "index.html"),
    "homepage_tile_new": ("Homepage — New Arrivals Tile", "single", "index.html"),
    "instagram_grid": ("Homepage — Instagram Grid", "multi", "index.html"),
    "men_hero": ("Men Page — Hero Banner", "single", "men.html"),
    "women_hero": ("Women Page — Hero Banner", "single", "women.html"),
    "collections_hero": ("Collections — Hero Banner", "single", "collections.html"),
    "blog_hero": ("Blog — Hero Banner", "single", "blog.html"),
    "blog_posts": ("Blog — Journal Entries (add as many as you like)", "multi", "blog.html"),
    "gallery_hero": ("Gallery — Hero Banner", "single", "gallery.html"),
    "gallery_grid": ("Gallery — Editorial Grid", "multi", "gallery.html"),
}

# gallery_grid photos are tagged with one of these so they participate in
# gallery.html's existing filter buttons (slug: display label).
GALLERY_CATEGORIES = {
    "studio": "Studio Product Shoot",
    "editorial": "Urban Editorial",
    "details": "Fabric & Craft",
}

# The 4 categories BHURA ships with. Distinguishes "original" departments (fixed
# clothing/shoe size sets apply) from anything admin adds later (free-text sizing).
DEFAULT_DEPARTMENTS = [("clothing", "Clothing"), ("shoes", "Shoes"), ("accessories", "Accessories"), ("sports", "Sports")]
DEFAULT_DEPARTMENT_NAMES = {name for _, name in DEFAULT_DEPARTMENTS}


class SiteImage(Base):
    """Every non-product photo on the storefront (hero banners, editorial sections,
    category tiles, the Instagram/gallery grids) — purely visual/marketing, never
    tied to a specific product. `slot` identifies which named spot an image fills;
    see SITE_IMAGE_SLOTS. Admin-managed so none of this ever needs a code change."""
    __tablename__ = "site_images"

    id = Column(Integer, primary_key=True)
    slot = Column(String(50), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    heading = Column(String(200), default="")
    subheading = Column(String(300), default="")
    link_url = Column(String(300), default="")   # where it goes on click, e.g. men.html
    tag = Column(String(50), nullable=True)        # optional category tag — used by gallery_grid
    width = Column(Integer, nullable=True)        # intended display dimensions in px —
    height = Column(Integer, nullable=True)        # frontend uses these for aspect-ratio when set
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


SUBSCRIBER_CATEGORIES = ["men", "women", "other", "all"]


class Subscriber(Base):
    """Newsletter/offer subscribers captured from the homepage signup form.
    `category` is their stated interest (men/women/other/all) so admin can
    segment who gets which offer email."""
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(20), default="all")
    subscribed_at = Column(DateTime(timezone=True), server_default=func.now())


class Image(Base):
    """Every uploaded photo's actual bytes, stored in the database itself rather
    than as a loose file on disk. This is the single source of truth — wherever
    the database goes (backup, restore, a new server), the photos go with it,
    with nothing that can fall out of sync. Product photos, site photos, the
    payment QR code, and customer-uploaded payment proofs all use this."""
    __tablename__ = "images"

    id = Column(Integer, primary_key=True)
    data = Column(LargeBinary, nullable=False)
    content_type = Column(String(100), default="image/jpeg")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
