from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


# ---------- Products ----------

class ImageOut(BaseModel):
    id: int
    url: str
    sort_order: int
    color_name: str | None = None
    model_config = ConfigDict(from_attributes=True)


class SiteImageOut(BaseModel):
    id: int
    slot: str
    url: str
    heading: str
    subheading: str
    link_url: str
    tag: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    sort_order: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class SiteImageUpdateIn(BaseModel):
    heading: Optional[str] = None
    subheading: Optional[str] = None
    link_url: Optional[str] = None
    tag: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ReviewOut(BaseModel):
    id: int
    product_id: int
    customer_name: str
    rating: int
    comment: str
    is_verified: bool  # True when order_id is set — computed, not stored directly
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, r):
        return cls(
            id=r.id, product_id=r.product_id, customer_name=r.customer_name,
            rating=r.rating, comment=r.comment, is_verified=r.order_id is not None,
            created_at=r.created_at,
        )


class ReviewIn(BaseModel):
    customer_name: str
    rating: int
    comment: str = ""
    order_number: str = ""   # optional — verifies purchase if it matches this product


class AdminReviewOut(ReviewOut):
    product_title: str = ""
    is_visible: bool = True


class ReturnRequestIn(BaseModel):
    reason: str
    email: str = ""
    phone: str = ""


class ReturnStatusIn(BaseModel):
    status: str
    admin_note: str = ""


class ReturnRequestOut(BaseModel):
    id: int
    order_id: int
    order_number: str = ""
    reason: str
    status: str
    admin_note: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ColorOut(BaseModel):
    id: int
    name: str
    hex_code: str
    model_config = ConfigDict(from_attributes=True)


class ColorIn(BaseModel):
    name: str
    hex_code: str = "#111111"


class VariantOut(BaseModel):
    id: int
    size: str
    color_name: str
    stock_qty: int
    model_config = ConfigDict(from_attributes=True)


class ProductCardOut(BaseModel):
    """Lightweight shape used in grid/listing views."""
    id: int
    slug: str
    title: str
    price: int
    compare_at_price: Optional[int] = None
    department: str = "Clothing"
    subcategory: str
    category_slug: str
    is_new_arrival: bool
    collection_tag: str
    primary_image: Optional[str] = None
    secondary_image: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ProductDetailOut(BaseModel):
    id: int
    slug: str
    title: str
    price: int
    compare_at_price: Optional[int] = None
    description: str
    material: str
    department: str = "Clothing"
    subcategory: str
    category_slug: str
    collection_tag: str
    is_new_arrival: bool
    images: list[ImageOut] = []
    colors: list[ColorOut] = []
    variants: list[VariantOut] = []
    avg_rating: Optional[float] = None
    review_count: int = 0
    model_config = ConfigDict(from_attributes=True)


class ProductIn(BaseModel):
    title: str
    category_slug: str          # gender: men | women
    department: str = "Clothing"  # Shoes | Clothing | Accessories | Sports
    subcategory: str = ""
    price: int
    compare_at_price: Optional[int] = None
    description: str = ""
    material: str = ""
    collection_tag: str = ""
    is_new_arrival: bool = False
    is_active: bool = True
    colors: list[str] = []             # simple list of color names, hex optional via /colors endpoint
    sizes: list[str] = []              # sizes to create as zero-stock variants if not already present


class ProductUpdateIn(BaseModel):
    title: Optional[str] = None
    category_slug: Optional[str] = None
    department: Optional[str] = None
    subcategory: Optional[str] = None
    price: Optional[int] = None
    compare_at_price: Optional[int] = None
    description: Optional[str] = None
    material: Optional[str] = None
    collection_tag: Optional[str] = None
    is_new_arrival: Optional[bool] = None
    is_active: Optional[bool] = None


class VariantIn(BaseModel):
    size: str
    color_name: str = ""
    stock_qty: int = 0


class CategoryOut(BaseModel):
    slug: str
    name: str
    count: int = 0
    model_config = ConfigDict(from_attributes=True)


class CategoryIn(BaseModel):
    slug: str
    name: str


class DepartmentOut(BaseModel):
    slug: str
    name: str
    count: int = 0
    is_default: bool = False
    model_config = ConfigDict(from_attributes=True)


class DepartmentIn(BaseModel):
    slug: str
    name: str


# ---------- Cart ----------

class CartItemIn(BaseModel):
    product_id: int
    color: str = ""
    size: str = ""
    quantity: int = 1


class CartItemUpdateIn(BaseModel):
    quantity: Optional[int] = None
    size: Optional[str] = None


class CartItemOut(BaseModel):
    id: int
    product_id: int
    slug: str
    title: str
    color: str
    color_hex: Optional[str] = None
    size: str
    quantity: int
    unit_price: int
    line_total: int
    image: Optional[str] = None
    max_stock: Optional[int] = None


class CartOut(BaseModel):
    items: list[CartItemOut]
    subtotal: int
    shipping_fee: int
    total: int
    item_count: int


# ---------- Orders ----------

class OrderCreateIn(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    address: str
    province: str
    city: str                    # District
    postal_code: str = ""
    payment_method: str          # "cod" | "mobile_banking"
    payment_reference: str = ""


class OrderItemOut(BaseModel):
    product_title: str
    color: str
    color_hex: Optional[str] = None
    size: str
    unit_price: int
    quantity: int
    line_total: int


class OrderOut(BaseModel):
    order_number: str
    status: str
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str
    province: str
    city: str
    postal_code: str
    payment_method: str
    subtotal: int
    shipping_fee: int
    total: int
    created_at: datetime
    items: list[OrderItemOut]
    email_sent: bool


class OrderAdminOut(OrderOut):
    id: int
    payment_reference: str
    payment_proof_path: str


class OrderStatusIn(BaseModel):
    status: str


# ---------- Admin auth ----------

class AdminLoginIn(BaseModel):
    username: str
    password: str


class AdminMeOut(BaseModel):
    username: str


# ---------- Settings ----------

class PublicSettingsOut(BaseModel):
    whatsapp_number: str
    merchant_name: str
    merchant_number: str
    qr_image_url: Optional[str] = None
    cod_enabled: bool
    mobile_banking_enabled: bool
    contact_phone: str = ""
    instagram_url: str = ""
    tiktok_url: str = ""


class SettingsUpdateIn(BaseModel):
    whatsapp_number: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_number: Optional[str] = None
    cod_enabled: Optional[bool] = None
    mobile_banking_enabled: Optional[bool] = None
    contact_phone: Optional[str] = None
    instagram_url: Optional[str] = None
    tiktok_url: Optional[str] = None


# ---------- Ledger (income/expenses) ----------

class ExpenseIn(BaseModel):
    category: str
    amount: int
    note: str = ""
    expense_date: date
    is_recurring: bool = False


class ExpenseUpdateIn(BaseModel):
    category: Optional[str] = None
    amount: Optional[int] = None
    note: Optional[str] = None
    expense_date: Optional[date] = None
    is_recurring: Optional[bool] = None


class ExpenseOut(BaseModel):
    id: int
    category: str
    amount: int
    note: str
    expense_date: date
    is_recurring: bool
    model_config = ConfigDict(from_attributes=True)


class LedgerSummaryOut(BaseModel):
    start_date: date
    end_date: date
    income_total: int
    order_count: int
    expense_total: int
    net: int
    expense_by_category: dict[str, int]


class SubscriberIn(BaseModel):
    email: str
    category: str = "all"


class SubscriberOut(BaseModel):
    id: int
    email: str
    category: str
    subscribed_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SendOfferIn(BaseModel):
    subscriber_ids: list[int]
    message: str
    subject: str = "A message from BHURA"
