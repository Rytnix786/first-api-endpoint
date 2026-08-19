# services/spam_service.py — Form Honeypot & Bot Defense Service

import logging

logger = logging.getLogger("SpamDefenseService")


class SpamDefenseService:
    @staticmethod
    def is_spam_submission(honeypot_value: str = None) -> bool:
        """
        Checks if submission is automated bot spam via honeypot detection.
        Legitimate human visitors will leave the hidden field blank.
        Bots auto-fill all form inputs.
        """
        if honeypot_value and len(honeypot_value.strip()) > 0:
            logger.warning(f"Spam detected: Honeypot field filled with value '{honeypot_value}'.")
            return True
        return False
