
from typing import List
from sqlalchemy.orm import Session
from .models import Subscription, Notification


def list_current_sub_symbols(session: Session) -> List[str]:
    result = session.query(Subscription.symbol) \
                .filter(Subscription.finished_at == None) \
                .distinct() \
                .all()

    return [
        values[0]
        for values in result
    ]


def list_current_subscriptions_from_symbol(session: Session, symbol: str) -> List[Subscription]:
    result = session.query(Subscription) \
                .filter(Subscription.finished_at == None) \
                .filter(Subscription.symbol == symbol.lower()) \
                .all()

    return result
