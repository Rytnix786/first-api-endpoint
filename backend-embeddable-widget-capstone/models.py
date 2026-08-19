# models.py — SQLAlchemy ORM Data Models for Embeddable Widget Platform

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Index,
    JSON
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(64), primary_key=True)  # e.g., 'tenant_acme'
    name = Column(String(128), nullable=False)
    api_key = Column(String(128), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    widgets = relationship("Widget", back_populates="tenant", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="tenant", cascade="all, delete-orphan")


class Widget(Base):
    __tablename__ = "widgets"

    id = Column(String(64), primary_key=True)  # e.g., 'w_demo_123'
    tenant_id = Column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(256), nullable=False, default="Join our Newsletter")
    description = Column(String(512), nullable=False, default="Get weekly updates delivered directly to your inbox.")
    button_text = Column(String(64), nullable=False, default="Subscribe Now")
    theme_color = Column(String(32), nullable=False, default="#4f46e5")
    allowed_origins = Column(Text, nullable=False, default="*")  # Comma-separated or '*'
    fields_config = Column(JSON, nullable=False, default=lambda: [
        {"name": "name", "type": "text", "label": "Full Name", "required": True},
        {"name": "email", "type": "email", "label": "Email Address", "required": True},
        {"name": "message", "type": "textarea", "label": "Note", "required": False}
    ])
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    tenant = relationship("Tenant", back_populates="widgets")
    submissions = relationship("Submission", back_populates="widget", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_widget_tenant_id", "tenant_id"),
    )


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String(64), primary_key=True, default=lambda: f"sub_{uuid.uuid4().hex[:12]}")
    tenant_id = Column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    widget_id = Column(String(64), ForeignKey("widgets.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    email = Column(String(256), nullable=False, index=True)
    message = Column(Text, nullable=True)
    ip_address = Column(String(64), nullable=False)
    country = Column(String(64), nullable=True)
    city = Column(String(64), nullable=True)
    geo_provider = Column(String(64), nullable=True)  # 'ip-api.com', 'ipapi.co', or None
    is_spam = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    tenant = relationship("Tenant", back_populates="submissions")
    widget = relationship("Widget", back_populates="submissions")

    __table_args__ = (
        Index("ix_submission_tenant_created", "tenant_id", "created_at"),
        Index("ix_submission_widget_created", "widget_id", "created_at"),
    )
