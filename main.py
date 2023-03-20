#!/usr/bin/env python3
# -*- encoding:utf-8 -*-

import argparse
import json
import os
import threading
import time
from collections import OrderedDict

from account import Accounts, Account
from api import app, globalObject, account_login_with_access_token, account_login_with_session_token


def load_config(config: dict, cache_path: str) -> Accounts:
    accounts = Accounts(cache_path)
    accounts.load(config)
    return accounts


def login_all(accounts: OrderedDict[str, Account]):
    for account_id in accounts:
        account = accounts[account_id]
        account_login_with_access_token(account)
        if not account.is_logged_in:
            account_login_with_session_token(account)
        time.sleep(2)


def run(host: str, port: int, dist: str, config: str, cache: str):
    from waitress import serve

    app._static_folder = dist
    with open(config, 'rb') as f:
        config_obj = json.load(f)
    accounts = load_config(config_obj, cache)
    globalObject.cache_path = cache
    globalObject.config_path = config
    globalObject.accounts = accounts
    for account_id in accounts.accounts:
        account = accounts.accounts[account_id]
        try:
            account.load_session(os.path.join(cache, account.id + ".json"))
        except FileNotFoundError:
            pass
    os.makedirs(cache, 0o755, True)
    threading.Thread(target=login_all, args=(accounts.accounts,)).start()
    for account_id in accounts.accounts:
        globalObject.default_account = accounts.accounts[account_id]
        break
    serve(app, host=host, port=port)


def main() -> int:
    home_path = os.getenv("HOME")
    parser = argparse.ArgumentParser(description="chatgpt web")
    parser.add_argument('--dist', '-d', type=str, help='ui dist path', default='./ui/dist')
    parser.add_argument('--host', '-o', type=str, help='host', default="127.0.0.1")
    parser.add_argument('--port', '-p', type=int, help='port', default=9987)
    parser.add_argument('--config', '-c', type=str, help='revChatGPT config.json',
                        default=os.path.join(home_path, ".config", "revChatGPT", "web.json"))
    parser.add_argument('--cache', '-e', type=str, help='cache directory',
                        default=os.path.join(home_path, ".cache", "revChatGPT"))
    args = parser.parse_args()
    run(args.host, args.port, args.dist, args.config, args.cache)
    return 0


if __name__ == "__main__":
    exit(main())
