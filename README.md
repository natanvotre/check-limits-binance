# CoinPanel Project

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

- Store ALL the loaded information from Binance subscriptions on databases
  - Millions of orders go through the Binance exchange every day.
  - It would overload our database really fast.
- Subscribe to ALL the Binance symbols at the same time because most of the symbols won't be needed.

We want to:

- Save/keep at max the last or last few orders from each symbol.
- Dinamically subscribe/unsubscribe from Binance symbols.
- Save the subscriptions to our system and update our database to send the correct data each time for the right subscriptions.
- Create a way to unsubscribe as well

We ought to do:

- Use FastAPI Websockets
- Use PostgreSQL/MongoDB for persistent data.
- Maybe split into 2 different microservices:
  - one for fetching
  - one for exposing
