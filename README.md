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
