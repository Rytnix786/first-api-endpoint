# models.py — SQLAlchemy ORM Data Models for Image Understanding & Content Matching Engine

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ImageItem(Base):
    __tablename__ = "images"

    id = Column(String(64), primary_key=True)  # e.g., 'img_fox_01'
    filename = Column(String(256), nullable=False)
    url = Column(String(512), nullable=True)
    subject = Column(String(128), nullable=False)       # e.g., 'red fox'
    category = Column(String(64), nullable=False)       # e.g., 'animal'
    attributes = Column(JSON, nullable=False, default=list)  # ['orange fur', 'wild', 'forest']
    caption = Column(Text, nullable=False)              # 'A red fox standing in a forest with autumn leaves'
    confidence = Column(Float, nullable=False)          # 0.0 to 1.0
    embedding = Column(JSON, nullable=True)             # List[float] embedding vector
    status = Column(String(32), default="processed", nullable=False)  # 'processed', 'flagged_low_confidence'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    reviews = relationship("ReviewLog", back_populates="image", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_images_subject", "subject"),
        Index("ix_images_category", "category"),
    )


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(String(64), primary_key=True)  # e.g., 'p_fox_01'
    title = Column(String(256), nullable=False)
    content = Column(Text, nullable=False)
    target_subject = Column(String(128), nullable=False)  # Expected primary subject e.g. 'red fox'
    embedding = Column(JSON, nullable=True)               # List[float] embedding vector
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    reviews = relationship("ReviewLog", back_populates="post", cascade="all, delete-orphan")


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id = Column(String(64), primary_key=True, default=lambda: f"rev_{uuid.uuid4().hex[:10]}")
    post_id = Column(String(64), ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    image_id = Column(String(64), ForeignKey("images.id", ondelete="CASCADE"), nullable=False, index=True)
    decision = Column(String(32), nullable=False)  # 'approved', 'rejected'
    reason = Column(Text, nullable=True)
    similarity_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    post = relationship("BlogPost", back_populates="reviews")
    image = relationship("ImageItem", back_populates="reviews")


class CostLog(Base):
    __tablename__ = "cost_logs"

    id = Column(String(64), primary_key=True, default=lambda: f"cost_{uuid.uuid4().hex[:10]}")
    operation = Column(String(64), nullable=False)  # 'vision_tagging', 'text_embedding'
    model_id = Column(String(64), nullable=False)
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    cost_micro_cents = Column(Integer, default=0, nullable=False)
    duration_ms = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
