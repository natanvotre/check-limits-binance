from os import environ
import mock
import random
import pytest
import json
import contextlib

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from threading import Thread

from sql import database
from sqlalchemy_utils import create_database, database_exists, drop_database
from websocket import WebSocketApp
from ingestion import Ingestion
from logger.logger import logging


@pytest.fixture
def connection():
    url = environ.get("TEST_DB_CONN")
    if not database_exists(url):
        create_database(url)

    engine = create_engine(url)
    yield engine.connect()
    drop_database(url)


@pytest.fixture
def setup_database(connection):
    database.Base.metadata.bind = connection
    database.Base.metadata.create_all()
    yield


@pytest.fixture
def db_session(setup_database, connection):
    with mock.patch.dict(environ, {"PSQL_CONN": environ.get("TEST_DB_CONN")}):
        yield scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=connection)
        )


@contextlib.contextmanager
def mock_websocketapp():
    def mocked_run_forever(self, *args, **kwargs) -> WebSocketApp:
        self.on_open(self)
        return self

    def mocked_send(self, data, opcode=None):
        logging.debug("Run mocked send")

    with mock.patch.object(WebSocketApp, 'run_forever', new=mocked_run_forever), \
         mock.patch.object(WebSocketApp, 'send', new=mocked_send):
        yield


def mock_trade_message(symbol: str, value: float):
    return json.dumps({
        "e": "trade",
        "s": symbol.upper(),
        "p": f"{value:.8f}",
        "q": random.random(),
        "m": False,
        "M": True,
        "b": random.randint(0, 100000000),
        "a": random.randint(0, 100000000),
        "T": random.randint(0, 100000000),
        "E": random.randint(0, 100000000),
        "t": random.randint(0, 100000000),
    })


def mock_subscription_message(symbol: str, threshold: float):
    return json.dumps({"symbol": symbol.lower(), "threshold": f"{threshold:.8f}"})


def run_until(func, timeout):
    t = Thread(target=func, name="ingestion")
    t.daemon = True
    t.start()
    t.join(timeout=timeout)


def mock_get_engine():
    db_credentials = environ.get("TEST_DB_CONN")
    return create_engine(db_credentials, pool_size=20, max_overflow=0)


TestIngestion = lambda: Ingestion(db_credentials=environ.get("TEST_DB_CONN"))
