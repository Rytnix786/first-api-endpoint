# seed.py — Database Seeding Script for Demo and Testing

import logging
from datetime import datetime, timezone
from database import SessionLocal, init_db
from models import Tenant, Widget, Submission

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SeedScript")


def seed_database():
    init_db()
    db = SessionLocal()
    try:
        # 1. Create Demo Tenant
        tenant = db.query(Tenant).filter(Tenant.id == "tenant_acme").first()
        if not tenant:
            tenant = Tenant(
                id="tenant_acme",
                name="Acme Corporation",
                api_key="ak_live_acme_secret_key_123"
            )
            db.add(tenant)
            db.commit()
            logger.info("Created Tenant: tenant_acme (API Key: ak_live_acme_secret_key_123)")

        # 2. Create Demo Widget
        widget = db.query(Widget).filter(Widget.id == "w_demo_123").first()
        if not widget:
            widget = Widget(
                id="w_demo_123",
                tenant_id="tenant_acme",
                title="Get Our 2026 Developer Report",
                description="Subscribe to receive our full engineering benchmarks directly to your inbox.",
                button_text="Download Free Report",
                theme_color="#4f46e5",
                allowed_origins="*"
            )
            db.add(widget)
            db.commit()
            logger.info("Created Widget: w_demo_123 (Tenant: tenant_acme)")

        # 3. Create Seed Submissions
        existing_subs = db.query(Submission).filter(Submission.widget_id == "w_demo_123").count()
        if existing_subs == 0:
            sub1 = Submission(
                tenant_id="tenant_acme",
                widget_id="w_demo_123",
                name="Sarah Jenkins",
                email="sarah.jenkins@techcorp.io",
                message="Looking forward to the architecture section.",
                ip_address="8.8.8.8",
                country="United States",
                city="Ashburn",
                geo_provider="ip-api.com",
                is_spam=False
            )
            sub2 = Submission(
                tenant_id="tenant_acme",
                widget_id="w_demo_123",
                name="Liam Smith",
                email="liam@cloudscale.uk",
                message="Great widget!",
                ip_address="1.1.1.1",
                country="Australia",
                city="Brisbane",
                geo_provider="ipapi.co",
                is_spam=False
            )
            sub3 = Submission(
                tenant_id="tenant_acme",
                widget_id="w_demo_123",
                name="Bot Spammer",
                email="spambot@promotions.xyz",
                message="Buy cheap followers",
                ip_address="192.0.2.1",
                country=None,
                city=None,
                geo_provider=None,
                is_spam=True
            )
            db.add_all([sub1, sub2, sub3])
            db.commit()
            logger.info("Created 3 initial seed submissions (including 1 spam entry).")

        logger.info("Database seeding completed successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
