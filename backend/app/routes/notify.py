from dotenv import load_dotenv
load_dotenv()

import logging
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import get_current_user, require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notify", tags=["Notify"])


# ==================== EMAIL CONFIG ====================
EMAIL_CONFIG = {
    "sender": os.getenv("SENDER_EMAIL"),
    "password": os.getenv("SENDER_PASSWORD"),
    "receiver": os.getenv("AUTHORITY_EMAIL"),
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587
}


class EscalationPayload(BaseModel):
    report_id: str
    hazard_type: str
    severity: str
    location: str


# ==================== EMAIL FUNCTION ====================
def send_email_alert(payload: EscalationPayload):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["sender"]
        msg['To'] = EMAIL_CONFIG["receiver"]
        msg['Subject'] = "⚡ EcoSnap Escalation Alert"

        body = f"""
        EcoSnap Escalation Alert

        Report ID: {payload.report_id}
        Hazard: {payload.hazard_type.replace('_', ' ').title()}
        Severity: {payload.severity.upper()}
        Location: {payload.location}
        Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

        Immediate action is required.
        """

        msg.attach(MIMEText(body, 'plain'))

        logger.info("Connecting to SMTP server...")

        server = smtplib.SMTP(
            EMAIL_CONFIG["smtp_server"],
            EMAIL_CONFIG["smtp_port"]
        )
        server.starttls()

        logger.info("Logging into email...")
        server.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])

        logger.info("Sending email...")
        server.send_message(msg)

        server.quit()

        logger.info(f"✅ Email sent to {EMAIL_CONFIG['receiver']}")
        return True

    except Exception as e:
        logger.error(f"❌ Email failed: {e}")
        return False


# ==================== API ROUTE ====================
@router.post("/escalation")
async def notify_escalation(
    payload: EscalationPayload,
    user: dict = Depends(get_current_user),
):
    require_admin(user)

    logger.info(
        f"[Escalation] report={payload.report_id} | "
        f"type={payload.hazard_type} | severity={payload.severity}"
    )

    # 🔍 DEBUG (VERY IMPORTANT)
    logger.info(f"EMAIL: {EMAIL_CONFIG['sender']}")
    logger.info(f"RECEIVER: {EMAIL_CONFIG['receiver']}")

    success = send_email_alert(payload)

    return {
        "success": success,
        "email_sent": success,
        "report_id": payload.report_id,
        "message": "Escalation processed"
    }


# ==================== RESOLVED NOTIFICATION ====================

class ResolvedPayload(BaseModel):
    report_id: str
    user_email: str
    hazard_type: str = "unknown"


def send_resolved_email(payload: ResolvedPayload) -> bool:
    """Send a resolution confirmation email to the report creator."""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["sender"]
        msg['To'] = payload.user_email
        msg['Subject'] = "✅ Your EcoSnap report has been resolved!"

        body = f"""
        Great news! Your EcoSnap hazard report has been resolved.

        Report ID: {payload.report_id}
        Hazard: {payload.hazard_type.replace('_', ' ').title()}
        Status: RESOLVED
        Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

        Thank you for making your community safer!
        — EcoSnap Team
        """

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
        server.starttls()
        server.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])
        server.send_message(msg)
        server.quit()

        logger.info(f"✅ Resolution email sent to {payload.user_email}")
        return True

    except Exception as e:
        logger.error(f"❌ Resolution email failed: {e}")
        return False


@router.post("/resolved")
async def notify_resolved(
    payload: ResolvedPayload,
    user: dict = Depends(get_current_user),
):
    """Admin-only: email the reporter when their report is resolved."""
    require_admin(user)

    logger.info(f"[Resolved] report={payload.report_id} | email={payload.user_email}")
    success = send_resolved_email(payload)

    return {
        "success": success,
        "email_sent": success,
        "report_id": payload.report_id,
        "message": "Resolution notification processed"
    }