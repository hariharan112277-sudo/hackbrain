"""
User Model — Frozen PostgreSQL schema contract mapping (table: users)
Track A (Database Layer) — Stage 1
"""

import uuid
from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class User(Base):
    __tablename__ = 'users'

    user_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(120))
    role = Column(String(20), nullable=False, server_default='viewer')  # Role options: admin, engineer, operator, viewer
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
