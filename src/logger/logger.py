import logging
import sys


logging.basicConfig(stream = sys.stdout,
                    filemode = "w",
                    format = "[%(asctime)s] – %(name)s – %(levelname)s: %(message)s",
                    level = logging.DEBUG)


class WsLogger:
    def __init__(self, conn_id: str) -> None:
        self.conn_id = conn_id

    def info(self, message: str, subs_id: str = None):
        subs_str = f"[{subs_id}]" if subs_id else ""
        logging.info(f"[{self.conn_id}]{subs_str}: {message}")

    def warn(self, message: str, subs_id: str = None):
        subs_str = f"[{subs_id}]" if subs_id else ""
        logging.warning(f"[{self.conn_id}]{subs_str}: {message}")

    def error(self, message: str, subs_id: str = None):
        subs_str = f"[{subs_id}]" if subs_id else ""
        logging.error(f"[{self.conn_id}]{subs_str}: {message}")

    def debug(self, message: str, subs_id: str = None):
        subs_str = f"[{subs_id}]" if subs_id else ""
        logging.debug(f"[{self.conn_id}]{subs_str}: {message}")
