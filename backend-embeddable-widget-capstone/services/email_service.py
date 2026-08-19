# services/email_service.py — Safe Email & Webhook Side Effect Service

import logging

logger = logging.getLogger("EmailService")


class EmailService:
    def __init__(self, simulate_failure: bool = False):
        self.simulate_failure = simulate_failure

    def send_submission_notification(self, recipient_email: str, widget_title: str, submitter_name: str, submitter_email: str) -> bool:
        """
        Sends lead notification email.
        CRITICAL RESILIENCE RULE: If this fails, it logs and returns False,
        never raising an unhandled exception that would crash the main submission path.
        """
        try:
            if self.simulate_failure:
                raise ConnectionRefusedError("SMTP Connection to mailserver:1025 timed out (Simulated Outage).")

            # Structured console log for local dev / testing
            logger.info(
                f"[NOTIFICATION EMAIL SENT] To: {recipient_email} | Subject: New Lead on '{widget_title}' | Lead: {submitter_name} ({submitter_email})"
            )
            return True

        except Exception as e:
            logger.error(f"[SIDE EFFECT RECOVERY] Failed to send email notification: {e}. Main submission remains successful.")
            return False
