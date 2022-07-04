import datetime
from os import environ
from typing import List
from uuid import uuid4

from sqlalchemy import (Column, String, DateTime, ForeignKey, Integer, Float)
from sqlalchemy.orm import relationship
from .database import Base

def uuid_str() -> str:
    return uuid4().hex[:8]


class Connection(Base):
    __tablename__ = "connections"

    id = Column(String(36), primary_key=True, unique=True, default=uuid_str)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    subscriptions = relationship("Subscription")

    def __repr__(self):
        return f"Connection(id={self.id!r}, created_at={self.created_at!r}, finished_at={self.finished_at!r})"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, unique=True, default=uuid_str)
    connection_id = Column(String(36), ForeignKey("connections.id"), nullable=False)
    symbol = Column(String, nullable=False)
    price_threshold = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    last_heartbeat = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"Subscription(id={self.id!r}, symbol={self.symbol!r}, price_threshold={self.price_threshold!r} created_at={self.created_at!r}, finished_at={self.finished_at!r})"

    def to_json(self):
        return {
            "id": self.id,
            "connection_id": self.connection_id,
            "symbol": self.symbol,
            "price_threshold": self.price_threshold,
            "created_at": self.created_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, unique=True, default=uuid_str)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=False)
    symbol = Column(String, nullable=False)
    message = Column(String, nullable=False)
    order_ref = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"Notification(id={self.id!r}, symbol={self.symbol!r}, created_at={self.created_at!r}, finished_at={self.finished_at!r})"

    def to_json(self):
        return {
            "id": self.id,
            "subscription_id": self.subscription_id,
            "symbol": self.symbol,
            "message": self.message,
            "order_ref": self.order_ref,
            "created_at": self.created_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }
