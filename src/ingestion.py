import json
from websocket import WebSocketApp

API_URL = "wss://stream.binance.com:9443/ws"

def on_error(ws: WebSocketApp, error: Exception):
    print(type(error))
    print(error)


def on_open(ws: WebSocketApp):
    # subscribe_example
    subscribe_to_ingestion(ws, 1, 'btcusdt')


def on_message(ws: WebSocketApp, message: str):
    print(f"Here is the message type: {message}")


def subscribe_to_ingestion(ws: WebSocketApp, id: int, symbol: str):
    message = {
        "method": "SUBSCRIBE",
        "params": [
            f"{symbol}@trade"
        ],
        "id": id,
    }
    print(message)
    ws.send(json.dumps(message))


def run_ingestion():

    ws = WebSocketApp(
        API_URL,
        on_error=on_error,
        on_open=on_open,
        on_message=on_message,
    )

    ws.run_forever()


if __name__ == "__main__":
    run_ingestion()