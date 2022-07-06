# noinspection PyUnresolvedReferences
import pytest
# noinspection PyUnresolvedReferences
from tests.base import db_session, setup_database, connection

import time
import logging
import random
import json

from datetime import datetime
from enums import Symbol
from fastapi.testclient import TestClient

from main import app, get_engine
from sql.models import Connection, Subscription, Notification
from tests.base import (
    mock_websocketapp, mock_trade_message, mock_subscription_message, mock_get_engine,
    TestIngestion, run_until
)


app.dependency_overrides[get_engine] = mock_get_engine


class TestIngestionFunctionally:
    # What do I need to test
    # - [x] Test if we can monitor the symbols we need to subscribe
    #   - [DB]: test database
    #   - [Ingestion]: mock init function to not really subscribe
    # - [x] Test if ingestion can subscribe only to existing symbols
    #   - [DB]: test database
    #   - [Ingestion]: real data
    # - [x] Test if ingestion can subscribe
    #   - [DB]: test database
    #   - [Ingestion]: real data
    # - [x] Test if ingestion can unsubscribe
    #   - [DB]: test database
    #   - [Ingestion]: real data

    def test_ingestion_can_receive_trade_message(self, db_session):
        """
            Test if ingestion can receive messages from Exchange

            Setup:
            - Mock WebSocketApp client simulating the messages received
              - We send mocked messages and ingestion figure out to read it

            Test:
            - Ingestion should be able to collect the current price and store into previous_prices dictionary

        """
        with mock_websocketapp():
            ingestion = TestIngestion()
            ws = ingestion.run()
            ws.on_message(ws, mock_trade_message(Symbol.BTCUSDT, 1000.00))

        assert ingestion.previous_prices == {Symbol.BTCUSDT: 1000.00}

    def test_ingestion_can_send_notification_when_price_goes_up(self, db_session):
        """
            Test if ingestion can send notification only when price goes up

            Setup:
            - Mock WebSocketApp client simulating the messages received
              - We send mocked messages and ingestion figure out to read it

            Test:
            - Ingestion should be able to create a notification row into database ONLY when price goes up
            - Added multiple subscriptions to make sure only the notification that has the correct threshold gets the
              notification
        """
        with mock_websocketapp():
            sub_btc_1000 = Subscription(symbol=Symbol.BTCUSDT, price_threshold="1000")
            sub_btc_1200 = Subscription(symbol=Symbol.BTCUSDT, price_threshold="1200")
            # another symbol to make sure we isolated from symbols
            sub_eth_1000 = Subscription(symbol=Symbol.ETHUSDT, price_threshold="1000")
            conn = Connection(
                subscriptions=[
                    sub_btc_1000,
                    sub_btc_1200,
                    sub_eth_1000,
                ]
            )
            db_session.add(conn)
            db_session.commit()

            ingestion = TestIngestion()
            ws = ingestion.run()

            # pricing going down - do not send any notification - from 1100 to 900
            ws.on_message(ws, mock_trade_message(Symbol.BTCUSDT, 1100.00))
            ws.on_message(ws, mock_trade_message(Symbol.BTCUSDT, 900.00))
            assert len(db_session.query(Notification).all()) == 0

            # pricing going up - do send a notification - from 900 to 1100
            ws.on_message(ws, mock_trade_message(Symbol.BTCUSDT, 1100.00))
            notifications = db_session.query(Notification).all()
            assert len(notifications) == 1
            assert notifications[0].subscription_id == sub_btc_1000.id

    def test_ingestion_can_send_notification_to_multiple_subscriptions(self, db_session):
        """
            Test if ingestion can send notification to multiple subscriptions at the same time

            Setup:
            - Mock WebSocketApp client simulating the messages received
              - We send mocked messages and ingestion figure out to read it

            Test:
            - Ingestion should be able to create notification rows into database when price goes up
            - Added two connections with one subscription each
            - Added different symbols to make sure it is isolated from symbols
        """
        with mock_websocketapp():
            sub_1_btc_1000 = Subscription(symbol=Symbol.BTCUSDT, price_threshold="1000")
            # another symbol to make sure we isolated from symbols
            sub_1_eth_1000 = Subscription(symbol=Symbol.ETHUSDT, price_threshold="1000")
            conn_1 = Connection(
                subscriptions=[
                    sub_1_btc_1000,
                    sub_1_eth_1000,
                ]
            )
            sub_2_btc_1000 = Subscription(symbol=Symbol.BTCUSDT, price_threshold="1000")
            # another symbol to make sure we isolated from symbols
            sub_2_eth_1000 = Subscription(symbol=Symbol.ETHUSDT, price_threshold="1000")
            conn_2 = Connection(
                subscriptions=[
                    sub_2_btc_1000,
                    sub_2_eth_1000,
                ]
            )
            db_session.add_all([conn_1, conn_2])
            db_session.commit()

            ingestion = TestIngestion()
            ws = ingestion.run()

            # Database is empty - no tricks here =D
            assert len(db_session.query(Notification).all()) == 0

            # pricing going up - do send notifications - from 900 to 1100
            ws.on_message(ws, mock_trade_message(Symbol.ETHUSDT, 900.00))
            ws.on_message(ws, mock_trade_message(Symbol.ETHUSDT, 1100.00))
            notifications = db_session.query(Notification).all()
            assert len(notifications) == 2
            for n in notifications:
                assert n.symbol == Symbol.ETHUSDT

    def test_ingestion_can_monitor_symbols(self, db_session):
        """
            Test if ingestion can monitor the symbols from database that needs to be subscribed

            Setup:
            - Test database
            - Mock WebSocketApp client simulating an actual run
              - on_open will run as well as the periodic background actions
              - it needs some time to run the background actions in order to replace the symbols to subscribe

            Test:
            - Ingestion should be able to add and remove into symbol_subs the symbols from the database subscriptions.
        """
        with mock_websocketapp():
            conn = Connection(
                subscriptions=[
                    Subscription(symbol=Symbol.BTCUSDT, price_threshold="1000")
                ]
            )
            db_session.add(conn)
            db_session.commit()

            assert len(db_session.query(Connection).all()) == 1

            ingestion = TestIngestion()
            ingestion.run()
            time.sleep(1)
            assert ingestion.symbol_subs == {Symbol.BTCUSDT}

            conn.subscriptions[0].finished_at = datetime.utcnow()
            db_session.add(conn)
            db_session.commit()

            time.sleep(1)
            assert ingestion.symbol_subs == set()

    def test_ingestion_can_subscribe_to_symbol(self, db_session):
        """
            [Real-time Test] Test if ingestion can subscribe and unsubscribe into the actual Exchange

            Setup:
            - Test database
            - Actual WebSocketApp client
              - running into a different thread with a timeout in order to collect enough data
              - it needs some time to subscribe and get real data - chose the most common symbols
              - it needs some time to run the background actions in order to replace the symbols to subscribe

            Test:
            - Ingestion should be able to subscribe into symbol
            - Ingestion should be able to collect the current prices from subscriptions
            - Ingestion should be able to unsubscribe
        """
        conn = Connection(
            subscriptions=[
                Subscription(symbol=Symbol.BTCUSDT, price_threshold="1000")
            ]
        )
        db_session.add(conn)
        db_session.commit()

        assert len(db_session.query(Connection).all()) == 1

        # run ingestion for 4 seconds with a BTCUSDT subscription
        ingestion = TestIngestion()
        run_until(ingestion.run, 4)

        # Should have gotten at least one price.
        assert set(ingestion.previous_prices.keys()) == {Symbol.BTCUSDT}

        # Turn off BTCUSDT subscription and turn on ETHUSDT
        conn.subscriptions[0].finished_at = datetime.utcnow()
        conn.subscriptions.append(Subscription(symbol=Symbol.ETHUSDT, price_threshold="2000"))
        db_session.add(conn)
        db_session.commit()

        # Run a bit more with to clean BTCUSDT messages out.
        run_until(ingestion.run, 1)
        # Cleaning up the prices but keeping the subscriptions
        ingestion.previous_prices = {}

        # run ingestion for 4 seconds with a ETHUSDT subscription
        run_until(ingestion.run, 4)

        # Should have only ETHUSDT subscribed
        assert ingestion.symbol_subs == {Symbol.ETHUSDT}
        # Now, since only ETHUSDT is subscribed, only prices from ETHUSDT is there.
        assert set(ingestion.previous_prices.keys()) == {Symbol.ETHUSDT}


class TestWsServerFunctionally:

    def test_ws_server_can_handle_multiple_subscriptions(self, db_session, caplog):
        """
            Test if WsServer can handle one and multiple subscriptions

            Setup:
            - Test database
            - Mock WsServer simulating a run

            Test:
            - Connect to WsServer and see the Connection being created into the database
            - Subscribe and see Subscriptions being created into the database
        """
        caplog.set_level(logging.DEBUG)
        client = TestClient(app)

        assert len(db_session.query(Connection).all()) == 0
        with client.websocket_connect("/ws") as websocket:
            time.sleep(0.1)
            assert len(db_session.query(Connection).all()) == 1
            assert len(db_session.query(Subscription).all()) == 0

            websocket.send_text(mock_subscription_message(symbol=Symbol.BTCUSDT, threshold=1000))
            websocket.receive_text()
            assert len(db_session.query(Subscription).all()) == 1

            websocket.send_text(mock_subscription_message(symbol=Symbol.ETHUSDT, threshold=2000))
            websocket.receive_text()
            assert len(db_session.query(Subscription).all()) == 2

    def test_ws_server_can_handle_notifications(self, db_session, caplog):
        """
            Test if WsServer can handle notifications

            Setup:
            - Test database
            - Mock WsServer simulating a run

            Test:
            - Connect to WsServer and see the Connection being created into the database
            - Subscribe and see Subscriptions being created into the database
            - Create a mock Notification on the database and check the message on websocket prompt
        """
        caplog.set_level(logging.DEBUG)
        client = TestClient(app)

        assert len(db_session.query(Connection).all()) == 0
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text(mock_subscription_message(symbol=Symbol.BTCUSDT, threshold=1000))
            websocket.receive_text()

            btc_sub = db_session.query(Subscription).all()[0]

            websocket.send_text(mock_subscription_message(symbol=Symbol.ETHUSDT, threshold=2000))
            websocket.receive_text()

            assert len(db_session.query(Subscription).all()) == 2

            notification = Notification(
                subscription_id=btc_sub.id,
                symbol=btc_sub.symbol,
                message="Mock message",
                order_ref=random.randint(0, 1000000)
            )
            db_session.add(notification)
            db_session.commit()

            res = json.loads(websocket.receive_text())
            assert res["subscription_id"] == btc_sub.id
            assert res["symbol"] == btc_sub.symbol
            assert res["message"] == "Mock message"

    def test_ws_server_cannot_subscribe_into_invalid_symbol(self, db_session, caplog):
        """
            Test if WsServer throw error when trying to subscribe into an invalid symbol

            Setup:
            - Test database
            - Mock WsServer simulating a run

            Test:
            - Connect to WsServer and see the Connection being created into the database
            - Subscribe and see Subscriptions being created into the database
        """
        caplog.set_level(logging.DEBUG)
        client = TestClient(app)

        assert len(db_session.query(Connection).all()) == 0
        with client.websocket_connect("/ws") as websocket:
            time.sleep(0.1)
            assert len(db_session.query(Connection).all()) == 1
            assert len(db_session.query(Subscription).all()) == 0

            websocket.send_text(mock_subscription_message(symbol="XXXXXX", threshold=1000))
            res = websocket.receive_text()
            assert len(db_session.query(Subscription).all()) == 0
            assert json.loads(res)["type"] == "error"

    def test_ws_server_notifications_shall_not_be_handled_by_a_different_subscription(self, db_session, caplog):
        """
            Test if WsServer throw error when trying to subscribe into an invalid symbol

            Setup:
            - Test database
            - Mock WsServer simulating a run

            Test:
            - Connect to WsServer and see the Connection being created into the database
            - Subscribe and see Subscriptions being created into the database
        """
        caplog.set_level(logging.DEBUG)
        client = TestClient(app)

        assert len(db_session.query(Connection).all()) == 0
        with client.websocket_connect("/ws") as w1, client.websocket_connect("/ws") as w2:
            w1.send_text(mock_subscription_message(symbol=Symbol.BTCUSDT, threshold=1000))
            w1.receive_text()

            w1_sub = db_session.query(Subscription).all()[0]

            w2.send_text(mock_subscription_message(symbol=Symbol.ETHUSDT, threshold=2000))
            w2.receive_text()

            assert len(db_session.query(Subscription).all()) == 2
            w2_sub = [s for s in db_session.query(Subscription).all() if s.symbol == Symbol.ETHUSDT][0]

            n1 = Notification(
                subscription_id=w1_sub.id,
                symbol=w1_sub.symbol,
                message="Mock message",
                order_ref=random.randint(0, 1000000)
            )
            n2 = Notification(
                subscription_id=w2_sub.id,
                symbol=w2_sub.symbol,
                message="Mock message 2",
                order_ref=random.randint(0, 1000000)
            )
            db_session.add_all([n1, n2])
            db_session.commit()

            res = json.loads(w1.receive_text())
            assert res["subscription_id"] == w1_sub.id
            assert res["symbol"] == w1_sub.symbol
            assert res["message"] == "Mock message"


class TestMockE2EIngestionAndWsServer:

    def test_e2e_with_mock_ingestion(self, db_session):
        """
            Test the communication between Ws Server and Ingestion using the database and Ingestion test, i.e. Ingestion
            with mocked WebSocketApp on send and run_forever.

            Setup:
            - Test database
            - Mock WebSocketApp client simulating an actual run of the Ingestion
              - on_open will run as well as the periodic background actions
              - it needs some time to run the background actions in order to replace the symbols to subscribe
            - Mock WsServer simulating a run

            Test:
            - WsServer can create connections and subscription based on the websocket connections and subscriptions
            - Ingestion can recognize the subscriptions created by WsServer and subscribe (even though it is mocked)
            into the Exchange (checked by symbol_subs)
              - The connection with the actual exchange is being tested at `test_ingestion_can_subscribe_to_symbol`
            - Receiving mock messages, Ingestion can detect rising price edges and create Notification rows into the
            database
            - WsServer can read the Notification rows and send the messages to the respective websocket connections
        """
        client = TestClient(app)
        assert len(db_session.query(Connection).all()) == 0
        with mock_websocketapp(), client.websocket_connect("/ws") as websocket:
            time.sleep(0.1)
            assert len(db_session.query(Connection).all()) == 1

            ingestion = TestIngestion()
            ws = ingestion.run()
            time.sleep(1)

            assert ingestion.symbol_subs == set()

            websocket.send_text(mock_subscription_message(symbol=Symbol.BTCUSDT, threshold=1000))
            websocket.receive_text()

            # Wait to the ingestion work
            time.sleep(1)

            subscriptions = db_session.query(Subscription).all()
            assert len(subscriptions) == 1
            assert ingestion.symbol_subs == {Symbol.BTCUSDT}

            # pricing going down - do not send any notification - from 1100 to 900
            ws.on_message(ws, mock_trade_message(Symbol.BTCUSDT, 1100.00))
            ws.on_message(ws, mock_trade_message(Symbol.BTCUSDT, 900.00))
            assert len(db_session.query(Notification).all()) == 0

            # pricing going up - do send a notification - from 900 to 1100
            ws.on_message(ws, mock_trade_message(Symbol.BTCUSDT, 1100.00))
            notifications = db_session.query(Notification).all()
            assert len(notifications) == 1

            message = websocket.receive_text()
            message = json.loads(message)
            assert message["subscription_id"] == subscriptions[0].id
