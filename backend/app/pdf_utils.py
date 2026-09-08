import io

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER


def build_receipt_pdf(order) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=24 * mm, bottomMargin=20 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    brand = ParagraphStyle("brand", parent=styles["Normal"], fontSize=22, leading=26, fontName="Helvetica-Bold", textColor=colors.HexColor("#111111"))
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=9, leading=13, textColor=colors.HexColor("#777777"))
    right_small = ParagraphStyle("right_small", parent=small, alignment=TA_RIGHT)
    h2 = ParagraphStyle("h2", parent=styles["Normal"], fontSize=12, leading=16, fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6)
    centered_small = ParagraphStyle("centered_small", parent=small, alignment=TA_CENTER)

    story = []
    story.append(Paragraph("BHURA", brand))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Wear Your Identity &nbsp;·&nbsp; Independent fashion label from Kathmandu", small))
    story.append(Spacer(1, 14))

    story.append(Paragraph(f"Receipt for Order #{order.order_number}", h2))
    meta_table = Table(
        [
            ["Order date", order.created_at.strftime("%d %b %Y, %H:%M")],
            ["Payment method", "Cash on Delivery" if order.payment_method == "cod" else "Mobile Banking (Fonepay/eSewa)"],
            ["Status", order.status.title()],
        ],
        colWidths=[120, 300],
    )
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#777777")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Ship to", h2))
    story.append(Paragraph(
        f"{order.first_name} {order.last_name}<br/>{order.address}<br/>{order.city} {order.postal_code}<br/>{order.phone} · {order.email}",
        styles["Normal"],
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Items", h2))
    data = [["Product", "Color / Size", "Qty", "Unit Price", "Line Total"]]
    for item in order.items:
        data.append([
            item.product_title, f"{item.color} / {item.size}", str(item.quantity),
            f"NPR {item.unit_price:,}", f"NPR {item.unit_price * item.quantity:,}",
        ])
    items_table = Table(data, colWidths=[160, 100, 40, 80, 90])
    items_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.HexColor("#111111")),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor("#EAEAEA")),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 8))

    totals = Table(
        [
            ["Subtotal", f"NPR {order.subtotal:,}"],
            ["Shipping", "Free" if order.shipping_fee == 0 else f"NPR {order.shipping_fee:,}"],
            ["Total", f"NPR {order.total:,}"],
        ],
        colWidths=[390, 90],
    )
    totals.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("LINEABOVE", (0, 2), (-1, 2), 0.75, colors.HexColor("#111111")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(totals)
    story.append(Spacer(1, 30))
    story.append(Paragraph("PROUDLY MADE IN NEPAL", centered_small))

    doc.build(story)
    return buffer.getvalue()
