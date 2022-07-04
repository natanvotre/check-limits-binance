
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from .models import Subscription, Notification

HEARTBEAT_LIMIT = 60


def list_current_sub_symbols(session: Session) -> List[str]:
    result = session.query(Subscription.symbol) \
                .filter(Subscription.finished_at == None) \
                .filter(Subscription.last_heartbeat > datetime.utcnow() - timedelta(seconds=HEARTBEAT_LIMIT)) \
                .distinct() \
                .all()

    return [
        values[0]
        for values in result
    ]


def list_current_subscriptions_from_symbol(session: Session, symbol: str) -> List[Subscription]:
    result = session.query(Subscription) \
                .filter(Subscription.finished_at == None) \
                .filter(Subscription.last_heartbeat > datetime.utcnow() - timedelta(seconds=HEARTBEAT_LIMIT)) \
                .filter(Subscription.symbol == symbol.lower()) \
                .all()

    return result


def list_subscriptions_from_connection(session: Session, conn_id: int) -> List[Subscription]:
    result = session.query(Subscription) \
                .filter(Subscription.finished_at == None) \
                .filter(Subscription.last_heartbeat > datetime.utcnow() - timedelta(seconds=HEARTBEAT_LIMIT)) \
                .filter(Subscription.connection_id == conn_id) \
                .all()

    return result


def list_notifications_from_subscription(session: Session, sub_id: int) -> List[Notification]:
    result = session.query(Notification) \
                .filter(Notification.finished_at == None) \
                .filter(Notification.subscription_id == sub_id) \
                .all()

    return result
