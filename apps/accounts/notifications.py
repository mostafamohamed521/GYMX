"""
GymX Notification Service
Handles all email (Gmail SMTP) and SMS (Twilio) communications.
"""
import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)



# ── SMS via Twilio ─────────────────────────────────────────
def send_sms(to_phone: str, message: str) -> bool:
    """Send SMS using Twilio. Returns True on success."""
    if not all([settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
                settings.TWILIO_PHONE_NUMBER]):
        logger.warning("Twilio credentials not configured — SMS not sent.")
        return False

    if not to_phone:
        logger.warning("No phone number provided — SMS not sent.")
        return False

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_phone,
        )
        logger.info(f"SMS sent to {to_phone} — SID: {msg.sid}")
        return True
    except Exception as e:
        logger.error(f"Twilio error sending to {to_phone}: {e}")
        return False



from typing import Union, List, Optional
# ── Email via Django/SMTP ──────────────────────────────────
def send_email(
    to: Union[str, List[str]],
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
) -> bool:
    """Send HTML email. Returns True on success."""
    if not to:
        return False

    recipients = [to] if isinstance(to, str) else to
    text = text_content or strip_tags(html_content)

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        logger.info(f"Email sent to {recipients} — Subject: {subject}")
        return True
    except Exception as e:
        logger.error(f"Email error to {recipients}: {e}")
        return False


# ── OTP Emails ─────────────────────────────────────────────
def send_otp_email(user, otp: str) -> bool:
    """Send email verification OTP."""
    subject = "GymX — Your Verification Code"
    html = _render_otp_email(
        name=user.get_short_name(),
        otp=otp,
        purpose="Email Verification",
        validity_minutes=10,
    )
    return send_email(user.email, subject, html)


def send_otp_sms(user, otp: str) -> bool:
    """Send OTP via SMS."""
    message = (
        f"GymX Verification Code: {otp}\n"
        f"Valid for 10 minutes. Do not share this code."
    )
    return send_sms(user.phone, message)


def send_otp(user, otp: str, channel: str = "both") -> dict:
    """
    Send OTP via email, SMS, or both.
    channel: 'email' | 'sms' | 'both'
    Returns dict with success status for each channel.
    """
    result = {"email": False, "sms": False}

    if channel in ("email", "both") and user.email:
        result["email"] = send_otp_email(user, otp)

    if channel in ("sms", "both") and user.phone:
        result["sms"] = send_otp_sms(user, otp)

    return result


# ── Password Reset ─────────────────────────────────────────
def send_password_reset_email(user, otp: str) -> bool:
    subject = "GymX — Password Reset Code"
    html = _render_otp_email(
        name=user.get_short_name(),
        otp=otp,
        purpose="Password Reset",
        validity_minutes=10,
        extra_note="If you did not request this, please ignore this email and your password will remain unchanged.",
    )
    return send_email(user.email, subject, html)


def send_password_reset_sms(user, otp: str) -> bool:
    message = (
        f"GymX Password Reset Code: {otp}\n"
        f"Valid 10 min. Ignore if you did not request this."
    )
    return send_sms(user.phone, message)


# ── Welcome Email ──────────────────────────────────────────
def send_welcome_email(user) -> bool:
    subject = f"Welcome to GymX, {user.get_short_name()}!"
    html = f"""
    {_email_header()}
    <div style="padding:32px 40px;">
      <h2 style="font-size:22px;font-weight:700;color:#0F172A;margin-bottom:8px;">
        Welcome to GymX, {user.get_short_name()}! 💪
      </h2>
      <p style="font-size:14px;color:#475569;line-height:1.7;margin-bottom:20px;">
        Your account has been created successfully. You now have access to the
        GymX Gym Management System.
      </p>
      <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:20px;margin-bottom:24px;">
        <div style="font-size:12px;font-weight:600;color:#94A3B8;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">Your Account Details</div>
        <div style="font-size:14px;color:#0F172A;margin-bottom:8px;"><strong>Name:</strong> {user.get_full_name()}</div>
        <div style="font-size:14px;color:#0F172A;margin-bottom:8px;"><strong>Username:</strong> {user.username}</div>
        <div style="font-size:14px;color:#0F172A;"><strong>Role:</strong> {user.get_role_display()}</div>
      </div>
      <a href="#" style="display:inline-block;background:#3B82F6;color:white;padding:12px 28px;border-radius:999px;font-size:14px;font-weight:600;text-decoration:none;">
        Access Dashboard
      </a>
    </div>
    {_email_footer()}
    """
    return send_email(user.email, subject, html)


# ── Login Alert ────────────────────────────────────────────
def send_login_alert_email(user, ip: str, browser: str = "Unknown") -> bool:
    """Alert user of a new login."""
    from django.utils import timezone
    subject = "GymX — New Login Detected"
    html = f"""
    {_email_header()}
    <div style="padding:32px 40px;">
      <h2 style="font-size:20px;font-weight:700;color:#0F172A;margin-bottom:8px;">New Login Detected</h2>
      <p style="font-size:14px;color:#475569;line-height:1.7;margin-bottom:20px;">
        Hi {user.get_short_name()}, we detected a new sign-in to your GymX account.
      </p>
      <div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:12px;padding:20px;margin-bottom:24px;">
        <div style="font-size:13px;color:#92400E;margin-bottom:8px;"><strong>Time:</strong> {timezone.now().strftime('%b %d, %Y at %H:%M')}</div>
        <div style="font-size:13px;color:#92400E;margin-bottom:8px;"><strong>IP Address:</strong> {ip}</div>
        <div style="font-size:13px;color:#92400E;"><strong>Browser:</strong> {browser}</div>
      </div>
      <p style="font-size:13px;color:#475569;">
        If this was you, no action needed. If not, please
        <a href="#" style="color:#3B82F6;font-weight:600;">change your password immediately</a>
        and enable Two-Factor Authentication.
      </p>
    </div>
    {_email_footer()}
    """
    return send_email(user.email, subject, html)


def send_login_alert_sms(user, ip: str) -> bool:
    from django.utils import timezone
    message = (
        f"GymX: New login from IP {ip} at "
        f"{timezone.now().strftime('%H:%M')}. "
        f"Not you? Change your password now."
    )
    return send_sms(user.phone, message)


# ── Membership Expiry ──────────────────────────────────────
def send_membership_expiry_email(user, expiry_date: str, days_left: int) -> bool:
    subject = f"GymX — Membership Expiring in {days_left} Days"
    html = f"""
    {_email_header()}
    <div style="padding:32px 40px;">
      <h2 style="font-size:20px;font-weight:700;color:#0F172A;margin-bottom:8px;">
        Your Membership is Expiring Soon
      </h2>
      <p style="font-size:14px;color:#475569;line-height:1.7;margin-bottom:20px;">
        Hi {user.get_short_name()}, your GymX membership will expire on
        <strong>{expiry_date}</strong> ({days_left} days remaining).
      </p>
      <a href="#" style="display:inline-block;background:#3B82F6;color:white;padding:12px 28px;border-radius:999px;font-size:14px;font-weight:600;text-decoration:none;">
        Renew Membership
      </a>
    </div>
    {_email_footer()}
    """
    return send_email(user.email, subject, html)


def send_membership_expiry_sms(user, days_left: int) -> bool:
    message = (
        f"GymX: Your membership expires in {days_left} days. "
        f"Visit us to renew and keep training!"
    )
    return send_sms(user.phone, message)


# ── Payment Confirmation ───────────────────────────────────
def send_payment_confirmation_email(user, amount: str, reference: str) -> bool:
    from django.utils import timezone
    subject = f"GymX — Payment Confirmed #{reference}"
    html = f"""
    {_email_header()}
    <div style="padding:32px 40px;">
      <div style="text-align:center;margin-bottom:28px;">
        <div style="width:56px;height:56px;background:#ECFDF5;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;margin-bottom:12px;">
          <span style="font-size:24px;">✓</span>
        </div>
        <h2 style="font-size:22px;font-weight:700;color:#065F46;">Payment Confirmed</h2>
      </div>
      <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:20px;margin-bottom:24px;">
        <div style="font-size:12px;font-weight:600;color:#94A3B8;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">Payment Details</div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #E2E8F0;font-size:14px;"><span style="color:#475569;">Amount</span><span style="font-weight:700;color:#0F172A;">{amount}</span></div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #E2E8F0;font-size:14px;"><span style="color:#475569;">Reference</span><span style="font-weight:600;color:#3B82F6;">#{reference}</span></div>
        <div style="display:flex;justify-content:space-between;padding:8px 0;font-size:14px;"><span style="color:#475569;">Date</span><span style="color:#0F172A;">{timezone.now().strftime('%b %d, %Y')}</span></div>
      </div>
      <p style="font-size:13px;color:#475569;text-align:center;">Thank you for your payment, {user.get_short_name()}. Keep up the great work!</p>
    </div>
    {_email_footer()}
    """
    return send_email(user.email, subject, html)


def send_payment_confirmation_sms(user, amount: str, reference: str) -> bool:
    message = (
        f"GymX Payment Confirmed! "
        f"Amount: {amount}, Ref: #{reference}. Thank you!"
    )
    return send_sms(user.phone, message)


# ── 2FA Alert ──────────────────────────────────────────────
def send_2fa_enabled_email(user) -> bool:
    subject = "GymX — Two-Factor Authentication Enabled"
    html = f"""
    {_email_header()}
    <div style="padding:32px 40px;">
      <h2 style="font-size:20px;font-weight:700;color:#0F172A;margin-bottom:8px;">2FA Enabled Successfully</h2>
      <p style="font-size:14px;color:#475569;line-height:1.7;margin-bottom:20px;">
        Hi {user.get_short_name()}, Two-Factor Authentication has been enabled on your GymX account.
        Your account is now more secure.
      </p>
      <div style="background:#ECFDF5;border:1px solid #A7F3D0;border-radius:12px;padding:16px;margin-bottom:20px;">
        <p style="font-size:13px;color:#065F46;margin:0;">
          🛡️ From now on, you'll need to enter a verification code every time you sign in.
        </p>
      </div>
      <p style="font-size:13px;color:#475569;">
        If you did not enable 2FA, please contact support immediately.
      </p>
    </div>
    {_email_footer()}
    """
    return send_email(user.email, subject, html)


# ── HTML Helpers ───────────────────────────────────────────
def _render_otp_email(
    name: str,
    otp: str,
    purpose: str = "Verification",
    validity_minutes: int = 10,
    extra_note: str = "",
) -> str:
    digits = list(otp)
    digit_boxes = "".join(
        f'<span style="display:inline-block;width:44px;height:54px;line-height:54px;'
        f'text-align:center;font-size:26px;font-weight:800;color:#1D4ED8;'
        f'background:#EFF6FF;border:2px solid #BFDBFE;border-radius:10px;margin:0 4px;">'
        f'{d}</span>'
        for d in digits
    )

    extra = f'<p style="font-size:12px;color:#94A3B8;margin-top:16px;">{extra_note}</p>' if extra_note else ""

    return f"""
    {_email_header()}
    <div style="padding:32px 40px;">
      <h2 style="font-size:22px;font-weight:700;color:#0F172A;margin-bottom:6px;">{purpose}</h2>
      <p style="font-size:14px;color:#475569;line-height:1.7;margin-bottom:28px;">
        Hi {name}, use the verification code below to complete your {purpose.lower()}.
      </p>

      <!-- OTP Boxes -->
      <div style="text-align:center;margin-bottom:28px;">
        {digit_boxes}
      </div>

      <!-- Timer notice -->
      <div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:12px;padding:14px 20px;margin-bottom:24px;text-align:center;">
        <p style="font-size:13px;color:#92400E;margin:0;">
          ⏱ This code expires in <strong>{validity_minutes} minutes</strong>.
          Do not share it with anyone.
        </p>
      </div>

      <p style="font-size:13px;color:#475569;">
        If you didn't request this code, you can safely ignore this email.
      </p>
      {extra}
    </div>
    {_email_footer()}
    """


def _email_header() -> str:
    return """
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
    <body style="margin:0;padding:0;background:#F0F4FF;font-family:'Helvetica Neue',Arial,sans-serif;">
    <div style="max-width:560px;margin:32px auto;background:white;border-radius:20px;overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.10);">

      <!-- Header -->
      <div style="background:linear-gradient(135deg,#1E3A8A,#1D4ED8);padding:24px 40px;text-align:center;">
        <div style="display:inline-flex;align-items:center;gap:10px;">
          <div style="width:36px;height:36px;background:rgba(255,255,255,0.15);border-radius:10px;display:inline-flex;align-items:center;justify-content:center;">
            <span style="color:white;font-size:18px;">🏋️</span>
          </div>
          <span style="font-size:22px;font-weight:800;color:white;letter-spacing:-0.5px;">GymX</span>
        </div>
      </div>
    """


def _email_footer() -> str:
    from django.utils import timezone
    return f"""
      <!-- Footer -->
      <div style="background:#F8FAFC;padding:20px 40px;border-top:1px solid #E2E8F0;text-align:center;">
        <p style="font-size:12px;color:#94A3B8;margin:0 0 6px;">
          © {timezone.now().year} GymX Management System. All rights reserved.
        </p>
        <p style="font-size:11px;color:#CBD5E1;margin:0;">
          This email was sent from an automated system. Please do not reply.
        </p>
      </div>
    </div>
    </body>
    </html>
    """
