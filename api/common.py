from multiprocessing import Event
from typing import Dict

from account import Account, Accounts


class GlobalObjectClass:
    def __init__(self):
        self.accounts: Accounts | None = None
        self.default_account: Account | None = None
        self.config_path: str = ""
        self.cache_path: str = ""

        # TODO 自动清理 messages
        self.messages: Dict[str, Dict] = {}
        self.stop_message_flag: Dict[str, Event] = {}


globalObject = GlobalObjectClass()
