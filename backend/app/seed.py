"""
Seeds the database on first run only (checks if any product already exists).
Product names, prices, and copy below are taken directly from the uploaded
BHURA mockup pages (index/men/product/cart/checkout). The five "Women" items
are placeholder catalog entries — the uploaded pages had no Women's page or
product data yet, so these exist so the Women nav link / page isn't empty.
Replace or edit any of it freely from the admin panel.
"""
from sqlalchemy.orm import Session

from . import models, config
from .auth import hash_password


def _img(photo_id: str) -> str:
    return f"https://images.unsplash.com/photo-{photo_id}?q=80&w=1200&auto=format&fit=crop"


MEN_PRODUCTS = [
    dict(
        title="Identity Boxy Hoodie", subcategory="Outerwear", price=8500,
        description="Heavyweight raw cotton fleece crafted with a structured architectural boxy fit. "
                     "Designed in Kathmandu for timeless urban endurance and uncompromising identity.",
        material="100% Heavyweight Raw Cotton (480 GSM)",
        collection_tag="drop-01-monolith", is_new_arrival=True,
        images=["1576995853123-5a10305d93c0", "1515886657613-9f3515b0c78f", "1509631179647-0177331693ae",
                "1552374196-1ab2a1c593e8", "1548883354-7622d03aca27", "1521572267360-ee0c2909d518",
                "1506794778202-cad84cf45f1d"],
        colors=[("Pitch Black", "#111111"), ("Charcoal Grey", "#444444"), ("Off-White", "#F7F7F5")],
    ),
    dict(
        title="Raw Concrete Bomber", subcategory="Outerwear", price=12500, compare_at_price=15000,
        description="A structured bomber silhouette in heavyweight shell fabric, built for raw urban "
                     "resilience with reinforced stitch detailing throughout.",
        material="Heavyweight Cotton-Nylon Blend Shell",
        collection_tag="drop-01-monolith", is_new_arrival=False,
        images=["1548883354-7622d03aca27", "1516257984-b1b4d707412e"],
        colors=[("Charcoal", "#3a3a3a")],
    ),
    dict(
        title="Monolith Heavy Tee", subcategory="Essentials", price=3400, compare_at_price=4200,
        description="A minimalist oversized tee in heavy-drape jersey. Precise boxy proportions with "
                     "monochromatic versatility — a BHURA everyday foundation piece.",
        material="220 GSM Combed Cotton Jersey",
        collection_tag="", is_new_arrival=True,
        images=["1521572267360-ee0c2909d518", "1583743814966-8936f5b7be1a"],
        colors=[("Off-White", "#F7F7F5")],
    ),
    dict(
        title="Kathmandu Utility Trouser", subcategory="Bottoms", price=7200,
        description="Structured cargo-utility trousers with a tapered leg and reinforced pocketing, "
                     "built for everyday urban movement.",
        material="Ripstop Cotton Canvas",
        collection_tag="", is_new_arrival=False,
        images=["1552374196-1ab2a1c593e8", "1503342217505-b0a15ec3261c"],
        colors=[("Black", "#111111")],
    ),
    dict(
        title="Himalayan Ribbed Knit", subcategory="Knitwear", price=9800,
        description="A dense ribbed knit inspired by high-altitude textures, cut with a relaxed "
                     "silhouette for layering through Kathmandu's cooler months.",
        material="Merino-Blend Ribbed Knit",
        collection_tag="drop-02-himalayan", is_new_arrival=False,
        images=["1506794778202-cad84cf45f1d", "1519085360753-af0119f7cbe7"],
        colors=[("Dark Grey", "#3f3f3f")],
    ),
    dict(
        title="Structural Overcoat", subcategory="Outerwear", price=16500,
        description="A long-line structural overcoat with a precise architectural shoulder line, cut "
                     "from a heavyweight wool-blend for cold-weather identity.",
        material="Wool-Blend Twill",
        collection_tag="drop-01-monolith", is_new_arrival=False,
        images=["1492562080023-ab3db95bfbce", "1509631179647-0177331693ae"],
        colors=[("Black", "#111111")],
    ),
]

WOMEN_PRODUCTS = [
    dict(
        title="Identity Oversized Hoodie", subcategory="Outerwear", price=8900,
        description="The women's cut of BHURA's signature hoodie — heavyweight raw cotton fleece in "
                     "an oversized, structured silhouette.",
        material="100% Heavyweight Raw Cotton (480 GSM)",
        collection_tag="drop-01-monolith", is_new_arrival=True,
        images=["1534528741775-53994a69daeb", "1509631179647-0177331693ae"],
        colors=[("Pitch Black", "#111111")],
    ),
    dict(
        title="Kathmandu Wide Trouser", subcategory="Bottoms", price=7500,
        description="A wide-leg utility trouser with a structured waistband and clean tapering, built "
                     "for everyday movement.",
        material="Ripstop Cotton Canvas",
        collection_tag="", is_new_arrival=False,
        images=["1552374196-1ab2a1c593e8", "1503342217505-b0a15ec3261c"],
        colors=[("Off-White", "#F7F7F5")],
    ),
    dict(
        title="Monolith Ribbed Knit", subcategory="Knitwear", price=9200,
        description="A dense ribbed knit with a relaxed, elongated fit — designed for layering through "
                     "cooler months.",
        material="Merino-Blend Ribbed Knit",
        collection_tag="drop-02-himalayan", is_new_arrival=True,
        images=["1519085360753-af0119f7cbe7", "1506794778202-cad84cf45f1d"],
        colors=[("Dark Grey", "#3f3f3f")],
    ),
    dict(
        title="Essentials Boxy Tee", subcategory="Essentials", price=3200,
        description="A boxy, heavy-drape everyday tee in monochrome jersey — the foundation of the "
                     "Identity Essentials line.",
        material="220 GSM Combed Cotton Jersey",
        collection_tag="", is_new_arrival=False,
        images=["1521572267360-ee0c2909d518", "1583743814966-8936f5b7be1a"],
        colors=[("Charcoal", "#3a3a3a")],
    ),
    dict(
        title="Structural Wool Coat", subcategory="Outerwear", price=15800,
        description="A long-line wool-blend coat with an architectural shoulder line, cut for "
                     "cold-weather identity.",
        material="Wool-Blend Twill",
        collection_tag="drop-01-monolith", is_new_arrival=False,
        images=["1492562080023-ab3db95bfbce", "1548883354-7622d03aca27"],
        colors=[("Black", "#111111")],
    ),
]

SIZES = ["S", "M", "L", "XL", "XXL"]
SHOE_SIZES = ["7", "8", "9", "10", "11"]
STOCK_BY_SIZE = {"S": 14, "M": 22, "L": 20, "XL": 12, "XXL": 6, "7": 8, "8": 12, "9": 14, "10": 10, "11": 6}

# New taxonomy demo products — Shoes / Accessories / Sports departments (the site previously
# only had Clothing). No stock photos on these yet: add real product photography via the
# admin panel when you actually stock these — left empty here rather than risk using
# mismatched or improperly-licensed placeholder imagery.
MEN_DEPARTMENT_DEMO_PRODUCTS = [
    dict(
        title="Monolith Runner", department="Shoes", subcategory="Sneakers", price=11500,
        description="A low-profile runner silhouette in structured technical mesh, built for "
                     "everyday movement through Kathmandu's streets.",
        material="Technical Mesh / Rubber Sole",
        collection_tag="", is_new_arrival=True, sizes=SHOE_SIZES,
        images=[], colors=[("Pitch Black", "#111111")],
    ),
    dict(
        title="Kathmandu Trail Boot", department="Shoes", subcategory="Boots", price=15800,
        description="A rugged trail-ready boot with reinforced ankle support for the city and "
                     "the hills beyond it.",
        material="Waxed Canvas / Leather Trim",
        collection_tag="", is_new_arrival=False, sizes=SHOE_SIZES,
        images=[], colors=[("Dark Grey", "#3f3f3f")],
    ),
    dict(
        title="Identity Canvas Tote", department="Accessories", subcategory="Bags", price=2800,
        description="A heavyweight canvas tote built to last, with the BHURA identity mark "
                     "printed on raw natural canvas.",
        material="Heavyweight Cotton Canvas",
        collection_tag="", is_new_arrival=True, sizes=["One Size"],
        images=[], colors=[("Natural", "#E8E2D0")],
    ),
    dict(
        title="BHURA Utility Cap", department="Accessories", subcategory="Headwear", price=1800,
        description="A structured six-panel cap in heavyweight twill with an embroidered identity mark.",
        material="Cotton Twill",
        collection_tag="", is_new_arrival=False, sizes=["One Size"],
        images=[], colors=[("Pitch Black", "#111111"), ("Off-White", "#F7F7F5")],
    ),
    dict(
        title="Performance Training Tee", department="Sports", subcategory="Running", price=3600,
        description="A moisture-wicking training tee cut for full range of motion, built for "
                     "running the ring road or the gym floor.",
        material="Recycled Polyester Performance Knit",
        collection_tag="", is_new_arrival=True,
        images=[], colors=[("Charcoal", "#3a3a3a")],
    ),
]

WOMEN_DEPARTMENT_DEMO_PRODUCTS = [
    dict(
        title="Monolith Runner (Women's)", department="Shoes", subcategory="Sneakers", price=11500,
        description="A low-profile runner silhouette in structured technical mesh, built for "
                     "everyday movement through Kathmandu's streets.",
        material="Technical Mesh / Rubber Sole",
        collection_tag="", is_new_arrival=True, sizes=SHOE_SIZES,
        images=[], colors=[("Off-White", "#F7F7F5")],
    ),
    dict(
        title="Identity Canvas Tote (Women's)", department="Accessories", subcategory="Bags", price=2800,
        description="A heavyweight canvas tote built to last, with the BHURA identity mark "
                     "printed on raw natural canvas.",
        material="Heavyweight Cotton Canvas",
        collection_tag="", is_new_arrival=False, sizes=["One Size"],
        images=[], colors=[("Natural", "#E8E2D0")],
    ),
    dict(
        title="Performance Training Tee (Women's)", department="Sports", subcategory="Running", price=3600,
        description="A moisture-wicking training tee cut for full range of motion.",
        material="Recycled Polyester Performance Knit",
        collection_tag="", is_new_arrival=True,
        images=[], colors=[("Dark Grey", "#3f3f3f")],
    ),
]


def _create_products(db: Session, category: models.Category, items: list[dict]) -> None:
    for item in items:
        product = models.Product(
            slug=_slugify(item["title"]),
            title=item["title"], category_id=category.id,
            department=item.get("department", "Clothing"),
            subcategory=item["subcategory"], price=item["price"],
            compare_at_price=item.get("compare_at_price"),
            description=item["description"], material=item["material"],
            collection_tag=item["collection_tag"], is_new_arrival=item["is_new_arrival"],
            is_active=True,
        )
        db.add(product)
        db.flush()

        for order, photo_id in enumerate(item["images"]):
            db.add(models.ProductImage(product_id=product.id, url=_img(photo_id), sort_order=order))

        for color_name, hex_code in item["colors"]:
            db.add(models.ProductColor(product_id=product.id, name=color_name, hex_code=hex_code))
            for size in item.get("sizes", SIZES):
                db.add(models.ProductVariant(
                    product_id=product.id, size=size, color_name=color_name,
                    stock_qty=STOCK_BY_SIZE.get(size, 15),
                ))


def _slugify(title: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def ensure_unisex_category(db: Session) -> None:
    """Runs on every startup (not just first seed) so existing databases pick up
    the Unisex category too, without needing a full re-seed or migration tool."""
    if not db.query(models.Category).filter(models.Category.slug == "unisex").first():
        db.add(models.Category(slug="unisex", name="Unisex"))
        db.commit()


DEFAULT_DEPARTMENTS = models.DEFAULT_DEPARTMENTS


def ensure_default_departments(db: Session) -> None:
    """Same pattern as ensure_unisex_category — runs every startup so existing
    databases get the Department lookup rows without a full re-seed."""
    if db.query(models.Department).first():
        return
    for slug, name in DEFAULT_DEPARTMENTS:
        db.add(models.Department(slug=slug, name=name))
    db.commit()


def seed_if_empty(db: Session) -> None:
    if db.query(models.Product).first():
        return  # already seeded

    men = models.Category(slug="men", name="Men")
    women = models.Category(slug="women", name="Women")
    unisex = models.Category(slug="unisex", name="Unisex")
    db.add_all([men, women, unisex])
    for slug, name in DEFAULT_DEPARTMENTS:
        db.add(models.Department(slug=slug, name=name))
    db.flush()

    _create_products(db, men, MEN_PRODUCTS)
    _create_products(db, women, WOMEN_PRODUCTS)
    _create_products(db, men, MEN_DEPARTMENT_DEMO_PRODUCTS)
    _create_products(db, women, WOMEN_DEPARTMENT_DEMO_PRODUCTS)

    if not db.query(models.AdminUser).first():
        db.add(models.AdminUser(
            username=config.DEFAULT_ADMIN_USERNAME,
            password_hash=hash_password(config.DEFAULT_ADMIN_PASSWORD),
        ))

    default_settings = {
        "whatsapp_number": config.WHATSAPP_DEFAULT,
        "merchant_name": "BHURA APPAREL",
        "merchant_number": "",
        "qr_image_path": "",
        "cod_enabled": "true",
        "mobile_banking_enabled": "true",
        "contact_phone": config.WHATSAPP_DEFAULT,
        "instagram_url": "",
        "tiktok_url": "",
    }
    for key, value in default_settings.items():
        db.add(models.SiteSetting(key=key, value=value))

    db.commit()
