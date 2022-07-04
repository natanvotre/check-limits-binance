import json
from os import environ
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from websocket import WebSocketApp
from sql.data import (list_current_sub_symbols, list_current_subscriptions_from_symbol)
from sql.models import Notification
from threading import Timer
from logger.logger import logging


class Ingestion:

    def __init__(self, api_url: str = None, db_credentials: str = None) -> None:
        self.api_url = api_url or environ.get("BINANCE_WS_URI")
        self.db_credentials = db_credentials or environ.get("PSQL_CONN")
        self.engine = create_engine(self.db_credentials,
                                    pool_size=20, max_overflow=0)
        self.sessionlocal: sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        # This holds the symbols we have already subscribed into the exchange.
        self.symbol_subs = {'etcusdt'}
        self.last_id = 1
        self.previous_prices = {}

    def on_error(self, ws: WebSocketApp, error: Exception):
        logging.error(error)

    def on_open(self, ws: WebSocketApp):
        self.check_current_subs_periodically(ws, 0.55)

    def on_message(self, ws: WebSocketApp, message: str):
        session: Session = self.sessionlocal()
        message = json.loads(message)
        logging.debug(f"[Message]: {json.dumps(message)}")

        if "e" not in message or message["e"] != "trade":
            session.close()
            return

        symbol = message["s"].lower()
        current_price = float(message["p"])
        previous_price = self.previous_prices.get(symbol, None)

        # Proceed if price rose
        if previous_price and previous_price < current_price:
            subs = list_current_subscriptions_from_symbol(session, symbol)
            # Publish Notification if current price surpassed the threshold
            notifications = [
                Notification(
                    subscription_id=sub.id,
                    symbol=sub.symbol,
                    message=f"Price has surpassed the threshold: {current_price}",
                    order_ref=int(message["E"])/1000
                )
                for sub in subs
                if previous_price < sub.price_threshold and sub.price_threshold < current_price
            ]
            session.add_all(notifications)
            session.commit()
            logging.info(f"publish notifications: {json.dumps([n.to_json() for n in notifications])}")

        self.previous_prices[symbol] = current_price
        session.close()

    def subscribe_to_ingestion(self, ws: WebSocketApp, id: int, symbol: str):
        message = {
            "method": "SUBSCRIBE",
            "params": [
                f"{symbol}@trade"
            ],
            "id": id,
        }
        logging.info(f"[Message]: {json.dumps(message)}")
        ws.send(json.dumps(message))
        self.symbol_subs.add(symbol)
        self.last_id = id

    def unsubscribe_to_ingestion(self, ws: WebSocketApp, id: int, symbol: str):
        message = {
            "method": "UNSUBSCRIBE",
            "params": [
                f"{symbol}@trade"
            ],
            "id": id,
        }
        logging.info(f"[Send]: {json.dumps(message)}")
        ws.send(json.dumps(message))
        self.symbol_subs.remove(symbol)
        self.last_id = id

    def check_current_subs_periodically(self, ws: WebSocketApp, period: float):

        self.check_current_subs(ws)
        thread = Timer(
            period,
            lambda: self.check_current_subs_periodically(ws, period)
        )
        thread.daemon = True
        thread.start()

    def check_current_subs(self, ws: WebSocketApp):
        session = self.sessionlocal()
        try:
            logging.debug("Checking subscriptions")

            open_symbols = set(list_current_sub_symbols(session))
            to_subscribe = open_symbols - self.symbol_subs
            to_unsubscribe = self.symbol_subs - open_symbols

            for symbol in to_subscribe:
                self.subscribe_to_ingestion(ws, self.last_id+1, symbol)

            for symbol in to_unsubscribe:
                self.unsubscribe_to_ingestion(ws, self.last_id+1, symbol)

            self.symbol_subs.update(to_subscribe)
            self.symbol_subs = self.symbol_subs - to_unsubscribe
        except Exception as e:
            logging.error(e)
        finally:
            session.close()

    def run(self):
        ws = WebSocketApp(
            self.api_url,
            on_error=self.on_error,
            on_open=self.on_open,
            on_message=self.on_message,
        )

        return ws.run_forever()


if __name__ == "__main__":
    Ingestion().run()
