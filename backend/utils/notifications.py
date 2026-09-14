"""
notifications.py — Budget alert emails (and SMS placeholder).

FIX APPLIED: previously, if GMAIL_USER/GMAIL_PASS weren't set, this would
attempt to connect to Gmail's SMTP with `None` credentials and throw an
unhandled exception. Since this is called from inside save_receipt() on
every single receipt save, that would have silently broken uploads for any
dev who hadn't set up email credentials. Now it checks first and skips
gracefully (logging a clear message) if not configured.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config.config import SMTP_SERVER, SMTP_PORT, GMAIL_USER, GMAIL_PASS
from utils.logger import log_info, log_error

ALERT_THRESHOLDS = [50, 90, 100]


def _alert_color(threshold: int) -> str:
    if threshold >= 100:
        return "#ef4444"   # red
    if threshold >= 90:
        return "#f97316"   # orange
    return "#f59e0b"       # amber


def send_email_alert(recipient_email: str, threshold: int, current_spend: float, budget: float) -> bool:
    """
    Sends a rich HTML budget alert email to the user via Gmail SMTP.
    Returns False (and logs) instead of raising if email isn't configured
    or sending fails, so callers never need to worry about this breaking
    the request that triggered it.
    """
    if not GMAIL_USER or not GMAIL_PASS:
        log_info(
            f"Email alerts not configured (GMAIL_USER/GMAIL_PASS missing) — "
            f"skipping {threshold}% alert for {recipient_email}."
        )
        return False

    color = _alert_color(threshold)
    pct = min((current_spend / budget * 100) if budget else 0, 100)
    remaining = max(budget - current_spend, 0)

    level_label = {
        50: "⚠️ Half-way Warning",
        90: "🚨 Critical Alert",
        100: "🔴 Budget Exceeded!",
    }.get(threshold, f"⚠️ {threshold}% Alert")

    subject = f"Receipt Vault: {level_label} — {threshold}% of budget used"

    html_body = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Inter,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:20px;overflow:hidden;
                    box-shadow:0 4px 24px rgba(0,0,0,0.08);">
        <tr>
          <td style="background:linear-gradient(135deg,{color},{color}cc);
                     padding:32px 40px;text-align:center;">
            <div style="font-size:2.8rem;">{("🔴" if threshold>=100 else "🚨" if threshold>=90 else "⚠️")}</div>
            <h1 style="color:#fff;margin:12px 0 4px;font-size:1.4rem;font-weight:800;">
              {level_label}
            </h1>
            <p style="color:rgba(255,255,255,0.85);margin:0;font-size:0.95rem;">
              Receipt Vault Analyzer — Monthly Budget Alert
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:36px 40px;">
            <p style="color:#374151;font-size:1rem;margin:0 0 24px;">
              Hi there,<br><br>
              Your spending this month has reached <strong style="color:{color};">{threshold}%</strong>
              of your set monthly budget. Here's a quick summary:
            </p>
            <table width="100%" cellpadding="0" cellspacing="8">
              <tr>
                <td style="background:#f9fafb;border-radius:12px;padding:16px 20px;text-align:center;">
                  <div style="color:#6b7280;font-size:0.78rem;font-weight:700;
                              text-transform:uppercase;letter-spacing:0.05em;">Spent This Month</div>
                  <div style="color:{color};font-size:1.5rem;font-weight:900;margin-top:6px;">
                    ₹{current_spend:,.2f}
                  </div>
                </td>
                <td width="16"></td>
                <td style="background:#f9fafb;border-radius:12px;padding:16px 20px;text-align:center;">
                  <div style="color:#6b7280;font-size:0.78rem;font-weight:700;
                              text-transform:uppercase;letter-spacing:0.05em;">Monthly Budget</div>
                  <div style="color:#1f2937;font-size:1.5rem;font-weight:900;margin-top:6px;">
                    ₹{budget:,.2f}
                  </div>
                </td>
                <td width="16"></td>
                <td style="background:#f9fafb;border-radius:12px;padding:16px 20px;text-align:center;">
                  <div style="color:#6b7280;font-size:0.78rem;font-weight:700;
                              text-transform:uppercase;letter-spacing:0.05em;">Remaining</div>
                  <div style="color:#10b981;font-size:1.5rem;font-weight:900;margin-top:6px;">
                    ₹{remaining:,.2f}
                  </div>
                </td>
              </tr>
            </table>
            <div style="margin:28px 0 8px;">
              <div style="display:flex;justify-content:space-between;
                          font-size:0.82rem;color:#6b7280;font-weight:600;margin-bottom:8px;">
                <span>Budget used</span>
                <span style="color:{color};font-weight:800;">{pct:.1f}%</span>
              </div>
              <div style="background:#e5e7eb;border-radius:99px;height:14px;overflow:hidden;">
                <div style="width:{pct:.1f}%;background:{color};
                            height:100%;border-radius:99px;"></div>
              </div>
            </div>
            <div style="background:#fef9c3;border:1px solid #fde68a;border-radius:12px;
                        padding:16px 20px;margin-top:24px;">
              <p style="margin:0;color:#92400e;font-size:0.9rem;font-weight:600;">
                💡 Tip: {"You've exceeded your budget! Avoid new expenses until next month." if threshold >= 100
                          else "You're very close to your limit. Review your recent expenses." if threshold >= 90
                          else "You're half-way through your budget. Consider slowing down spending."}
              </p>
            </div>
          </td>
        </tr>
        <tr>
          <td style="background:#f9fafb;padding:20px 40px;text-align:center;
                     border-top:1px solid #e5e7eb;">
            <p style="margin:0;color:#9ca3af;font-size:0.78rem;">
              This is an automated alert from <strong>Receipt Vault Analyzer</strong>.<br>
              You are receiving this because a budget threshold was reached on your account ({recipient_email}).
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"Receipt Vault Analyzer <{GMAIL_USER}>"
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, recipient_email, msg.as_string())
        server.quit()
        log_info(f"Budget alert ({threshold}%) sent to {recipient_email}")
        return True
    except Exception as e:
        log_error(f"Failed to send email alert to {recipient_email}: {e}")
        return False


def send_sms_alert(phone_number: str, threshold: int, current_spend: float) -> bool:
    """
    Placeholder for SMS alerts. Wire up Twilio (or similar) here when ready —
    for now this just logs, so it never fails a request.
    """
    message = f"Budget Alert: {threshold}% of your monthly limit reached. Spent: ₹{current_spend:,.2f}"
    log_info(f"SMS Alert (not sent - no provider configured) to {phone_number}: {message}")
    return True
