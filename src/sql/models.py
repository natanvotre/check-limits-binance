import datetime
from os import environ
from typing import List
from uuid import uuid4

from sqlalchemy import (Column, String, DateTime, ForeignKey, Integer, Float)
from .database import Base, SessionLocal

def uuid_str() -> str:
    return str(uuid4())


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, unique=True, default=uuid_str)
    symbol = Column(String, nullable=False)
    price_threshold = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"Subscription(id={self.id!r}, symbol={self.symbol!r}, price_threshold={self.price_threshold!r} created_at={self.created_at!r}, finished_at={self.finished_at!r})"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, unique=True, default=uuid_str)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=False),
    symbol = Column(String, nullable=False)
    message = Column(String, nullable=False)
    order_ref = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"Notification(id={self.id!r}, symbol={self.symbol!r}, created_at={self.created_at!r}, finished_at={self.finished_at!r})"
