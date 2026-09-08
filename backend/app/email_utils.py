import smtplib
import logging
from email.message import EmailMessage

from . import config

logger = logging.getLogger("bhura.email")


def smtp_configured() -> bool:
    return bool(config.SMTP_HOST and config.SMTP_USER and config.SMTP_PASSWORD)


def send_order_confirmation(to_email: str, order_number: str, html_body: str, pdf_bytes: bytes | None = None) -> bool:
    """
    Sends the order confirmation email with the PDF receipt attached.
    Returns True if a send was attempted and succeeded, False if skipped/failed.
    Never raises: a checkout should never fail because email delivery failed.
    """
    if not smtp_configured():
        logger.info(
            "SMTP not configured (set SMTP_HOST/SMTP_USER/SMTP_PASSWORD in .env) — "
            "skipping email for order %s. Receipt PDF was still generated on disk.",
            order_number,
        )
        return False

    try:
        msg = EmailMessage()
        msg["Subject"] = f"Order Confirmation & Receipt #{order_number} — BHURA"
        msg["From"] = f"{config.SMTP_FROM_NAME} <{config.SMTP_FROM}>"
        msg["To"] = to_email
        msg.set_content("Your BHURA order has been received. View this email in an HTML-capable client for the full receipt.")
        msg.add_alternative(html_body, subtype="html")

        if pdf_bytes:
            msg.add_attachment(
                pdf_bytes, maintype="application", subtype="pdf",
                filename=f"BHURA-Receipt-{order_number}.pdf",
            )

        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception:
        logger.exception("Failed to send order confirmation email for order %s", order_number)
        return False


def send_simple_email(to_email: str, subject: str, html_body: str) -> bool:
    """Generic HTML email sender for notifications that aren't the order receipt
    (e.g. return-request updates). Same graceful-skip-if-unconfigured behavior as
    send_order_confirmation, and never raises."""
    if not smtp_configured():
        logger.info("SMTP not configured — skipping email '%s' to %s", subject, to_email)
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{config.SMTP_FROM_NAME} <{config.SMTP_FROM}>"
        msg["To"] = to_email
        msg.set_content("View this email in an HTML-capable client.")
        msg.add_alternative(html_body, subtype="html")
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception:
        logger.exception("Failed to send email '%s' to %s", subject, to_email)
        return False


def _email_shell(inner_html: str) -> str:
    """Shared BHURA-branded wrapper so every notification email looks consistent."""
    return f"""
    <div style="font-family:Helvetica,Arial,sans-serif;max-width:560px;margin:0 auto;color:#111;">
      <div style="background:#111;color:#fff;padding:24px;text-align:center;letter-spacing:2px;">
        <h1 style="margin:0;font-size:20px;">BHURA</h1>
      </div>
      <div style="padding:24px;">
        {inner_html}
        <p style="color:#777;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-top:24px;">Proudly Made in Nepal</p>
      </div>
    </div>
    """


RETURN_STATUS_MESSAGES = {
    "requested": "We've received your return request and will review it shortly.",
    "approved": "Your return has been approved. Please follow the return shipping instructions we've shared, or contact us if you need them resent.",
    "rejected": "After review, we're unable to accept this return. Please contact us if you have questions.",
    "received": "We've received your returned item(s) and they're being inspected.",
    "refunded": "Your refund has been processed. It may take a few business days to reflect depending on your payment method.",
}


def render_offer_email_html(message: str) -> str:
    # message may contain the admin's own line breaks — preserve them as <br> since
    # this is plain text composed in a textarea, not HTML.
    safe_message = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    return _email_shell(f"""
        <div style="font-size:13px;color:#333;line-height:1.6;">{safe_message}</div>
    """)


def render_return_email_html(order, return_request) -> str:
    message = RETURN_STATUS_MESSAGES.get(return_request.status, "Your return status has been updated.")
    return _email_shell(f"""
        <h2 style="font-size:16px;">Return update for order #{order.order_number}</h2>
        <p style="color:#555;font-size:13px;">Hi {order.first_name}, here's an update on your return request.</p>
        <table style="width:100%;font-size:13px;margin-top:12px;border-collapse:collapse;">
          <tr><td style="padding:6px 0;color:#777;">Status</td><td style="padding:6px 0;text-align:right;font-weight:bold;text-transform:capitalize;">{return_request.status}</td></tr>
          <tr><td style="padding:6px 0;color:#777;">Reason given</td><td style="padding:6px 0;text-align:right;">{return_request.reason}</td></tr>
        </table>
        <p style="color:#555;font-size:13px;margin-top:16px;">{message}</p>
        {f'<p style="color:#555;font-size:13px;margin-top:8px;"><strong>Note from BHURA:</strong> {return_request.admin_note}</p>' if return_request.admin_note else ''}
    """)


def render_order_email_html(order) -> str:
    rows = "".join(
        f"""
        <tr>
          <td style="padding:8px 0;border-bottom:1px solid #EAEAEA;">{item.product_title}<br>
              <span style="color:#777;font-size:11px;">{item.color} / {item.size} × {item.quantity}</span></td>
          <td style="padding:8px 0;border-bottom:1px solid #EAEAEA;text-align:right;">NPR {item.unit_price * item.quantity:,}</td>
        </tr>"""
        for item in order.items
    )
    return f"""
    <div style="font-family:Helvetica,Arial,sans-serif;max-width:560px;margin:0 auto;color:#111;">
      <div style="background:#111;color:#fff;padding:24px;text-align:center;letter-spacing:2px;">
        <h1 style="margin:0;font-size:20px;">BHURA</h1>
      </div>
      <div style="padding:24px;">
        <h2 style="font-size:16px;">Thank you, {order.first_name}!</h2>
        <p style="color:#555;font-size:13px;">Your order <strong>#{order.order_number}</strong> has been received and is being processed.</p>
        <table style="width:100%;border-collapse:collapse;font-size:13px;margin-top:16px;">
          {rows}
        </table>
        <table style="width:100%;font-size:13px;margin-top:12px;">
          <tr><td>Subtotal</td><td style="text-align:right;">NPR {order.subtotal:,}</td></tr>
          <tr><td>Shipping</td><td style="text-align:right;">{'Free' if order.shipping_fee == 0 else f'NPR {order.shipping_fee:,}'}</td></tr>
          <tr><td style="font-weight:bold;padding-top:6px;">Total</td><td style="text-align:right;font-weight:bold;padding-top:6px;">NPR {order.total:,}</td></tr>
        </table>
        <p style="color:#555;font-size:13px;margin-top:20px;">Shipping to:<br>
          {order.address}, {order.city} {order.postal_code}</p>
        <p style="color:#777;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-top:24px;">Proudly Made in Nepal</p>
      </div>
    </div>
    """
