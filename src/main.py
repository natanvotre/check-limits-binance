from os import environ
import json
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sql.models import Subscription, Connection
from sql.data import list_subscriptions_from_connection, list_notifications_from_subscription, HEARTBEAT_LIMIT
from logger.logger import WsLogger
from enums import Symbol

app = FastAPI()


def get_engine():
    db_credentials = environ.get("PSQL_CONN")
    return create_engine(db_credentials, pool_size=20, max_overflow=0)


class WsHandler():

    def __init__(self, websocket: WebSocket, engine) -> None:
        self.websocket = websocket
        self.engine = engine
        self.sessionlocal: sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        conn = Connection()
        session = self.sessionlocal()
        session.add(conn)
        session.commit()
        self.conn_id = conn.id
        self.logger = WsLogger(self.conn_id)
        session.close()

    async def check_notifications(self):
        session = self.sessionlocal()
        subs = list_subscriptions_from_connection(session, self.conn_id)

        for sub in subs:
            if sub.last_heartbeat < datetime.utcnow() - timedelta(seconds=HEARTBEAT_LIMIT/2):
                sub.last_heartbeat = datetime.utcnow()

                self.logger.debug("Subscription heartbeat updated", sub.id)
            notifications = list_notifications_from_subscription(session, sub.id)
            for notification in notifications:
                message = json.dumps(notification.to_json())
                await self.websocket.send_text(message)
                self.logger.debug(message)
                notification.finished_at = datetime.utcnow()
            session.add_all(notifications)
        session.commit()
        session.close()


    async def handle_received_message(self, data: str):
        # Check if it is a json
        data = json.loads(data)
        # Only subscribes
        # TODO: Handle multiple commands on websockets
        data["threshold"] = float(data["threshold"])
        session = self.sessionlocal()
        subs = list_subscriptions_from_connection(session, self.conn_id)
        self.logger.debug(f"previous subscriptions: {[json.dumps(sub.to_json()) for sub in subs]}")

        # Check if received symbol is valid
        if data["symbol"].lower() not in Symbol.__dict__.values():
            error_res = json.dumps({"type": "error", "message": "symbol is not valid, check https://www.binance.com/api/v3/exchangeInfo to get the available symbols"})
            await self.websocket.send_text(error_res)
            return error_res

        for sub in subs:
            if sub.price_threshold == data["threshold"] and sub.symbol == data["symbol"]:
                return

        sub = Subscription(
            symbol=data["symbol"],
            connection_id=self.conn_id,
            price_threshold=data["threshold"],
        )
        session.add(sub)
        session.commit()

        res = sub.to_json()
        await self.websocket.send_text(json.dumps(res))
        self.logger.info(json.dumps(res), subs_id=sub.id)
        session.close()
        return res

    def close_websocket_session(self):
        session = self.sessionlocal()
        for conn in session.query(Connection).filter(Connection.id == self.conn_id).all():
            conn.finished_at = datetime.utcnow()
        for sub in session.query(Subscription).filter(Subscription.connection_id == self.conn_id).all():
            sub.finished_at = datetime.utcnow()
        session.commit()
        session.close()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    handler = WsHandler(websocket, get_engine())
    logger = handler.logger
    logger.debug(handler.engine.url)
    while True:
        try:
            data = await asyncio.wait_for(websocket.receive_text(), 0.5)
            await handler.handle_received_message(data)
        # Connection closed
        except WebSocketDisconnect:
            handler.close_websocket_session()
            return
        # No commands received, proceeds
        except asyncio.TimeoutError:
            logger.debug("No message received")
        except Exception as e:
            logger.error(e)
            await websocket.send_text('Invalid json subscription message. e.g: {"symbol": "btcusdt", "threshold": "20356.11"}')
            logger.info('Invalid json subscription message. e.g: {"symbol": "btcusdt", "threshold": "20356.11"}')

        # Check the notification messages and consume them
        await handler.check_notifications()
