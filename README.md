# CoinPanel Project

## Description

This is my humble solution for the CoinPanel test for ingest and digest of binance market data.

- WebSocket server is done in FastAPI, since you guys told me that this is one of the technologies used.
- Ingestion in a python code using websocketclient and multi-threading for handling the subscriptions
- Database is being managed using SQL Alchemy ORM.

This project is basically divided into 3 pieces:

- **Ingestion**
  - Subscribe on-demand into binance API on different trade symbols
  - Collect the information, check if values surpassed the subscriptions threshold.
  - "Publish" the Notification items
- **WebSocketServer**
  - Client is able to subscribe into symbol+threshold
  - Publish the subscription into the database.
  - Send the Notifications according to the subscription.
- **Database**
  - Communication channel between WebSocketServer and Ingestion
  - WebSocketServer creates the Connections and Subscriptions
  - Ingestion handles the Subscriptions and creates Notifications
  - WebSocketServer consumes the Notifications

## How to run

### Virtual environment

- Setup venv and install the requirements

```
python3.8 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

- Run database

```
docker-compose up postgres -d
```

- Export the env vars from .env file

```
export $(cat .env | xargs)
```

- Run both Ingestion and WebSocketServer:

```
python src/ingestion.py & uvicorn main:app --app-dir src --reload --host 0.0.0.0
```

### Docker Compose

Run the docker-compose file with `postgres`, `ingestion`, and `webserver` services:

```
docker-compose up postgres ingestion webserver
```

## How to Test

### Pytest

#### Virtual environment

- Do the steps on how to run, except the last command.
- Apply the pytest:

```
pytest src/tests/*
```

#### Docker Compose

Run the docker-compose file with `postgres` and `testing` services:

```
docker-compose up postgres testing
```

## Requirements

### Part 1

- Build an ingestion pipeline for binance market data via this websocket stream.
- https://github.com/binance/binance-spot-api-docs/blob/master/websocket-streams.md#trade-streams

- **Rules**:
  - You can use pre-built components, but must be able to handle
    introduction of new symbols to be monitored.

### Part 2

- Build a simple system which allows the user to enter a symbol and a
number, and based on the symbol and a number, monitor the market data
and print out every time the price goes above the input number.

- Solution should be provided in a containerized format - Dockerfile, along with other dependencies.
- For the interview, please come prepared to answer questions about
limitations, scalability and recoverability of the designed system.

- Commit the above to a public github and provide the link.

## Project

### Assumptions

We don't want to:

- [x] Store ALL the loaded information from Binance subscriptions on databases
  - Millions of orders go through the Binance exchange every day.
  - It would overload our database really fast.
- [x] Subscribe to ALL the Binance symbols at the same time because most of the symbols won't be needed.

We want to:

- [x] Save/keep at max the last or last few orders from each symbol.
  - [x] kept the last order into a dict
    - Bad for scaling, I know. But when the time comes, we should shard the subscription among all the instances.
- [x] Dinamically subscribe/unsubscribe from Binance symbols.
- [x] Save the subscriptions to our system and update our database to send the correct data each time for the right subscriptions.
- [ ] Create a way to unsubscribe as well
  - It is only accepting subscription for now

We ought to:

- [x] Use FastAPI Websockets
- [x] Use PostgreSQL/MongoDB for persistent data.
- [x] Maybe split into 2 different microservices:
  - one for fetching
  - one for exposing

## Caveats:

- Pytest is somehow breaking in the end some connections left opened.
  So when you run all test cases, you might see Exception taking place, but all test cases are passing.
- WebsocketServer is only accepting `subscribe` messages, but there is a note showing where
  we need to change to add multiple commands (e.g. unsubscribe, listMySubs, fancyDataAboutAllSubs).
